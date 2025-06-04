from django.shortcuts import render, redirect
from event.models import Event
from user.models import Order, Payement
from .forms import TicketOrderForm
from .notchpay import NotchPay, get_operator
from django.conf import settings
from .utils import process_order
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A6
from reportlab.lib.utils import ImageReader
from io import BytesIO
from django.http import HttpResponse
import qrcode
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
import hmac
import hashlib
import json
from django.core.mail import EmailMessage

def index(request):
    events = Event.objects.all()
    
    return render(request, "sale/index.html", context={
        "events": events
    })

def event_detail(request, pk, slug):
    event = Event.objects.get(id=pk)
    return render(request, "sale/detail.html", context={
        "event": event
    })


def ticket_order(request):
    if request.method == 'POST':
        form = TicketOrderForm(request.POST)
        if form.is_valid():
            if not request.user.is_authenticated:
                request.session['pending_order'] = {
                    'ticket_type': form.cleaned_data['ticket_type'],
                    'quantity': form.cleaned_data['quantity'],
                }
                return redirect(f'/login')
            return process_order(request, form.cleaned_data)
    else:
        form = TicketOrderForm()
    return render(request, "sale/detail.html", {'form': form})


def order_page(request, id):
    try:
        order = Order.objects.get(id=id)
    except Order.DoesNotExist:
        return HttpResponse("Commande introuvable", status=404)
    return render(request, "sale/order_detail.html", {"order": order})

def generate_ticket(request, order):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A6)

    for ticket in order.ticket_set.all():
        qr_data = request.build_absolute_uri(reverse('ticket_validate', args=[ticket.identifier]))
        qr_img = qrcode.make(qr_data)
        qr_buffer = BytesIO()
        qr_img.save(qr_buffer, format='PNG')
        qr_buffer.seek(0)
        qr_reader = ImageReader(qr_buffer)
    
        p.setFont("Helvetica-Bold", 14)
        p.drawString(60, 260, f"TICKET: {ticket.type.event.name}")

        p.setFont("Helvetica", 10)
        p.drawString(20, 230, f"Identifiant : {ticket.identifier}")
        p.drawString(20, 215, f"Type : {ticket.type.name}")
        p.drawString(20, 200, f"Prix : {ticket.type.price} XAF")
        p.drawString(20, 185, f"Statut : {ticket.status}")
        p.drawString(20, 170, f"Événement : {ticket.type.event.name}")
        p.drawString(20, 155, f"Date : {ticket.type.event.time_start.strftime('%d/%m/%Y')}")

        if order.user:
            p.drawString(20, 140, f"Acheteur : {order.user.username}")
            p.drawString(20, 125, f"Téléphone : {order.user.phone}")

        p.drawImage(qr_reader, 130, 40, width=80, height=80)
        p.setFont("Helvetica-Oblique", 8)
        p.drawString(20, 100, "Merci pour votre achat !")
        p.showPage()  # ➕ Important : nouvelle page pour chaque ticket

    p.save()
    buffer.seek(0)
    return buffer

def payment_sucess(request, reference=None):
    reference = reference or request.GET.get('reference')
    print(reference)
    order = Order.objects.filter(reference=reference).all()[0]
    amount = 0
    for ticket in order.ticket_set.all():
        ticket.status = "pay"
        amount += ticket.type.price
        ticket.save()
    order.status = "completed"
    order.save()

    payment = Payement()
    payment.amount = amount
    payment.operator = get_operator(order.user.phone)
    payment.payement_date = datetime.now()
    payment.order = order
    payment.save()

    buffer = generate_ticket(request, order)
    pdf_data = buffer.getvalue()

    email = EmailMessage(
        subject='Vos billets',
        body='Bonjour, veuillez trouver en pièce jointe vos billets au format PDF.',
        from_email='lefakongdilane@gmail.com',
        to=[order.user.email],
    )
    email.attach(f'tickets_commande_{order.pk}.pdf', pdf_data, 'application/pdf')
    email.send()
    print("okay")

    return HttpResponse("Payment valide")

def download_ticket(request, order_id):
    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        return HttpResponse("Commande introuvable", status=404)
    
    buffer = generate_ticket(request, order)
    pdf_data = buffer.getvalue()

    email = EmailMessage(
        subject='Vos billets',
        body='Bonjour, veuillez trouver en pièce jointe vos billets au format PDF.',
        from_email='lefakongdilane@gmail.com',
        to=[order.user.email],
    )
    email.attach(f'tickets_commande_{order.pk}.pdf', pdf_data, 'application/pdf')
    email.send()

    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="tickets_commande_{order.pk}.pdf"'
    return response

def validate_ticket(request):
    pass


# Fonction de vérification de la signature
def verify_webhook_signature(payload, signature, secret):
    calculated_signature = hmac.new(
        secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(calculated_signature, signature)


@csrf_exempt
def notchpay_webhook(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)

    signature = request.headers.get('X-Notch-Signature')
    payload = request.body  # bytes

    if not signature:
        return JsonResponse({'error': 'Signature manquante'}, status=400)

    secret = settings.NOTCHPAY_WEBHOOK_SECRET  # Définis ceci dans settings.py

    if not verify_webhook_signature(payload, signature, secret):
        return JsonResponse({'error': 'Signature invalide'}, status=400)

    try:
        event = json.loads(payload.decode('utf-8'))
        print(event)
        if event['event'] == 'payment.complete':
            payment_sucess(request, event['data']['reference'])
            print("Événement reçu :", event)
        elif event['event'] == 'payment.failed':
            order = Order.objects.get(reference=event['data']['reference'])
            subject = "Action requise : Échec du paiement pour votre commande"
            message = f"""
            Bonjour {order.user.username},

            Nous avons constaté que le paiement de votre commande (Référence: {order.reference}) n'a pas abouti.

            Détails de la commande :
            - Événement : {order.ticket_set.first().type.event.name}
            - Montant total : {order.total_amount} XAF
            - Date de la commande : {order.created_at.strftime('%d/%m/%Y')}

            Pour finaliser votre achat, veuillez cliquer sur le lien ci-dessous :
            http://ticky.com/order/{order.id}

            Si vous rencontrez des difficultés, n'hésitez pas à nous contacter.

            Cordialement,
            L'équipe Ticky
            """

            email = EmailMessage(
                subject=subject,
                body=message,
                from_email='lefakongdilane@gmail.com',
                to=[order.user.email],
            )
            email.send()
            print("payment failed")
        elif event['event'] == 'payment.canceled':
            order = Order.objects.get(reference=event['data']['reference'])
            for ticket in order.ticket_set.all():
                ticket.status = 'nopay'
                ticket.save()
            order.status = 'canceled'
            order.save()
            print("payment canceled")
        else:
            pass

        return HttpResponse("Webhook reçu", status=200)
    except json.JSONDecodeError as e:
        print(e)
        return JsonResponse({'error': 'Payload JSON invalide'}, status=400)
