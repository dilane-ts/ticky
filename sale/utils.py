from event.models import TypeTicket, Ticket
from user.models import Order
import uuid
from .notchpay import NotchPay
from django.shortcuts import redirect
from django.conf import settings
from .exceptions import NotchPayError
from django.shortcuts import render
from django.contrib import messages

def process_order(request, cleaned_data):
    ticket_type_id = cleaned_data['ticket_type']
    quantity = cleaned_data['quantity']

    type_ticket = TypeTicket.objects.get(id=ticket_type_id)
    order = Order(user=request.user)
    order.save()
    error = None

    for _ in range(quantity):
        ticket = Ticket()
        ticket.identifier = 'ti_' + str(uuid.uuid4())
        ticket.type = type_ticket
        ticket.order = order
        ticket.save()
    
    order = Order.objects.get(id=order.pk)
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