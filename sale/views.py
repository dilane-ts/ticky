from django.shortcuts import render, redirect
from event.models import Event
from user.models import Order, Payement
from .forms import TicketOrderForm
from .notchpay import NotchPay, get_operator
from django.conf import settings
from .utils import process_order
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
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
from .exceptions import NotchPayError
from .utils import NotchPay
from django.contrib import messages

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
                return redirect('register')
            return process_order(request, form.cleaned_data)
    else:
        form = TicketOrderForm()
    return render(request, "sale/detail.html", {'form': form})

def checkout(request, pk):
    error = None
    try:
        order = Order.objects.get(pk=pk)
    except Order.DoesNotExist as e:
        return HttpResponse("Order don't exists", status=404)

    amount = 0
    for ticket in order.ticket_set.all():
        amount += ticket.type.price
    try:
        notchpay = NotchPay(settings.NOTCHPAY_PUBLIC_API_KEY, order)
        notchpay.initialize(request, amount)
        notchpay.complete()
    except NotchPayError as e:
        error = e.message
        messages.error(request, error)
    
    return render(request, 'sale/order_detail.html', {
        'order': order,
        'error': error
    })


def order_page(request, id):
    try:
        order = Order.objects.get(id=id)
    except Order.DoesNotExist:
        return HttpResponse("Commande introuvable", status=404)
    return render(request, "sale/order_detail.html", {"order": order})

def generate_ticket(request, order):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    
    # Couleurs
    purple_color = HexColor('#8B5CF6')  # Violet comme dans l'image
    green_color = HexColor('#10B981')   # Vert pour "Payé"
    gray_color = HexColor('#6B7280')    # Gris pour les labels
    light_gray = HexColor('#F3F4F6')    # Gris clair pour les fonds
    total_amount = 0
    for ticket in order.ticket_set.all():
        total_amount += ticket.type.price

    for ticket in order.ticket_set.all():
        # Dimensions de la page
        width, height = A4
        
        # Header violet avec coin arrondi (simulé)
        p.setFillColor(purple_color)
        p.rect(40, height-120, width-80, 60, fill=1, stroke=0)
        
        # Badge "Terminé" 
        p.setFillColor(green_color)
        p.roundRect(width-150, height-110, 80, 25, 12, fill=1, stroke=0)
        p.setFillColor(white)
        p.setFont("Helvetica-Bold", 10)
        p.drawCentredString(width-110, height-100, "Terminé")
        
        # Titre de la commande
        p.setFillColor(white)
        p.setFont("Helvetica-Bold", 14)
        command_text = f"Commande #{order.id}"
        p.drawString(60, height-95, command_text)
        
        # Section Informations client
        y_pos = height - 160
        p.setFillColor(black)
        p.setFont("Helvetica-Bold", 12)
        p.drawString(60, y_pos, "Informations client")
        
        # Fond gris clair pour la section client
        p.setFillColor(light_gray)
        p.rect(40, y_pos-80, width-80, 70, fill=1, stroke=0)
        
        # Informations utilisateur
        p.setFillColor(gray_color)
        p.setFont("Helvetica", 10)
        y_pos -= 20
        p.drawString(60, y_pos, "Nom d'utilisateur")
        p.drawString(320, y_pos, "Email")
        
        p.setFillColor(black)
        p.setFont("Helvetica-Bold", 11)
        y_pos -= 15
        p.drawString(60, y_pos, order.user.username if order.user else "Anonyme")
        p.drawString(320, y_pos, order.user.email if order.user else "N/A")
        
        p.setFillColor(gray_color)
        p.setFont("Helvetica", 10)
        y_pos -= 20
        p.drawString(60, y_pos, "Téléphone")
        # p.drawString(320, y_pos, "Rôle")
        
        p.setFillColor(black)
        p.setFont("Helvetica-Bold", 11)
        y_pos -= 15
        p.drawString(60, y_pos, order.user.phone if order.user and hasattr(order.user, 'phone') else "N/A")
        # p.drawString(320, y_pos, "User")
        
        # Section Billets commandés
        y_pos -= 40
        p.setFillColor(black)
        p.setFont("Helvetica-Bold", 12)
        p.drawString(60, y_pos, "Billets commandés")
        
        # Fond gris clair pour la section ticket
        p.setFillColor(light_gray)
        p.rect(40, y_pos-180, width-80, 170, fill=1, stroke=0)
        
        # Titre de l'événement
        y_pos -= 25
        p.setFillColor(black)
        p.setFont("Helvetica-Bold", 14)
        event_title = f"{ticket.type.event.name}"
        # if hasattr(ticket.type.event, 'description') and ticket.type.event.description:
        #     event_title += f" - {ticket.type.event.description}"
        p.drawString(60, y_pos, event_title)
        
        # Informations du ticket en deux colonnes
        y_pos -= 25
        p.setFillColor(gray_color)
        p.setFont("Helvetica", 10)
        p.drawString(60, y_pos, "Type de billet")
        p.drawString(320, y_pos, "Identifiant")
        
        p.setFillColor(black)
        p.setFont("Helvetica-Bold", 11)
        y_pos -= 15
        p.drawString(60, y_pos, ticket.type.name)
        
        # Cadre pour l'identifiant (comme dans l'image)
        p.setStrokeColor(gray_color)
        p.setFillColor(white)
        p.rect(320, y_pos-7, 200, 20, fill=1, stroke=1)
        p.setFillColor(black)
        p.setFont("Courier", 9)
        p.drawString(325, y_pos, ticket.identifier)
        
        # Lieu et dates
        y_pos -= 30
        p.setFillColor(gray_color)
        p.setFont("Helvetica", 10)
        p.drawString(60, y_pos, "Lieu")
        p.drawString(320, y_pos, "Dates")
        
        p.setFillColor(black)
        p.setFont("Helvetica-Bold", 11)
        y_pos -= 15
        venue = getattr(ticket.type.event, 'venue', 'Lieu à confirmer')
        p.drawString(60, y_pos, venue)
        p.drawString(320, y_pos, ticket.type.event.time_start.strftime('%d %b %Y'))
        
        # Statut et prix
        y_pos -= 25
        p.setFillColor(gray_color)
        p.setFont("Helvetica", 10)
        p.drawString(60, y_pos, "Statut du billet")
        p.drawString(320, y_pos, "Prix")
        
        y_pos -= 15
        # Badge de statut
        if ticket.status.lower() == 'paid' or ticket.status.lower() == 'payé':
            p.setFillColor(green_color)
            p.roundRect(58, y_pos-5, 40, 18, 9, fill=1, stroke=0)
            p.setFillColor(white)
            p.setFont("Helvetica-Bold", 9)
            p.drawString(68, y_pos, "Payé")
        else:
            p.setFillColor(black)
            p.setFont("Helvetica-Bold", 11)
            p.drawString(60, y_pos, ticket.status)
        
        # Prix en couleur violette
        p.setFillColor(purple_color)
        p.setFont("Helvetica-Bold", 14)
        p.drawString(320, y_pos, f"{ticket.type.price} FCFA")
        
        # QR Code
        qr_data = request.build_absolute_uri(reverse('ticket_validate', args=[ticket.identifier]))
        qr_img = qrcode.make(qr_data, box_size=4, border=2)
        qr_buffer = BytesIO()
        qr_img.save(qr_buffer, format='PNG')
        qr_buffer.seek(0)
        qr_reader = ImageReader(qr_buffer)
        
        # Placer le QR code en bas à droite
        p.drawImage(qr_reader, width - 180, y_pos - 30, width=80, height=80)
        
        # Section Informations de paiement
        y_pos -= 120
        p.setFillColor(black)
        p.setFont("Helvetica-Bold", 12)
        p.drawString(60, y_pos, "Informations de paiement")
        
        # Tableau de paiement
        y_pos -= 25
        p.setFillColor(gray_color)
        p.setFont("Helvetica", 10)
        p.drawString(60, y_pos, "Opérateur")
        p.drawString(200, y_pos, "Montant")
        p.drawString(340, y_pos, "Date de paiement")
        
        p.setFillColor(black)
        p.setFont("Helvetica-Bold", 11)
        y_pos -= 15
        payment_method = getattr(order, 'payment_method', 'MTN')
        p.drawString(60, y_pos, payment_method)
        p.setFillColor(green_color)
        p.drawString(200, y_pos, f"{total_amount} FCFA")
        p.setFillColor(black)
        payment_date = order.created_at.strftime('%d %b %Y') if hasattr(order, 'created_at') else "N/A"
        p.drawString(340, y_pos, payment_date)
        
        # Total de la commande
        y_pos -= 40
        p.setFillColor(black)
        p.setFont("Helvetica-Bold", 12)
        p.drawString(60, y_pos, "Total de la commande")
        p.setFillColor(purple_color)
        p.setFont("Helvetica-Bold", 18)
        p.drawRightString(width-60, y_pos, f"{total_amount} FCFA")
        
        # Message de remerciement
        p.setFillColor(gray_color)
        p.setFont("Helvetica-Oblique", 10)
        p.drawCentredString(width/2, 80, "Merci pour votre achat ! Présentez ce ticket à l'entrée.")
        
        p.showPage()  # Nouvelle page pour chaque ticket
    
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
        elif event['event'] in ['payment.failed', 'payment.expired']:
            order = Order.objects.get(reference=event['data']['reference'])
            order.status = 'failed'
            order.save()
            total_amount = 0
            for ticket in order.ticket_set.all():
                total_amount += ticket.type.price

            subject = "Action requise : Échec du paiement pour votre commande"
            message = f"""
            Bonjour {order.user.username},

            Nous avons constaté que le paiement de votre commande (Référence: {order.reference}) n'a pas abouti.

            Détails de la commande :
            - Événement : {order.ticket_set.first().type.event.name}
            - Montant total : {total_amount} XAF
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
        elif event['event'] == 'payment.cancelled':
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
