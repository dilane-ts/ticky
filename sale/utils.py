from event.models import TypeTicket, Ticket
from user.models import Order
import uuid
from django.shortcuts import redirect

def process_order(request, cleaned_data):
    ticket_type_id = cleaned_data['ticket_type']
    quantity = cleaned_data['quantity']

    type_ticket = TypeTicket.objects.get(id=ticket_type_id)
    order = Order(user=request.user)
    order.save()

    for _ in range(quantity):
        ticket = Ticket()
        ticket.identifier = 'ti_' + str(uuid.uuid4())
        ticket.type = type_ticket
        ticket.order = order
        ticket.save()
    
    
    return redirect(f'/checkout/{order.pk}')