from django.shortcuts import render, redirect
from event.models import Event, TypeTicket, Ticket
from user.models import Order, User
from .forms import TicketOrderForm
import uuid
from .notchpay import NotchPay
from django.conf import settings
from .utils import process_order

def index(request):
    events =Event.objects.all()
    return render(request, "sale/index.html", context={
        "events": events
    })

def event_detail(request, pk):
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
            process_order(request, form.cleaned_data)
    else:
        form = TicketOrderForm()
    return render(request, "sale/detail.html", {'form': form})



def checkout_order(request, id):
    if request.method == 'GET':
        order = Order.objects.get(id=id)
        amount = 0
        for ticket in order.ticket_set.all():
            amount += ticket.type.price
        notchpay = NotchPay(settings.NOTCHPAY_PUBLIC_API_KEY, order)
        notchpay.initialize(amount)
        notchpay.complete()
        
        return render(request, "sale/checkout.html")
        
