from django import forms
from event.models import TypeTicket

class TicketOrderForm(forms.Form):
    ticket_type = forms.IntegerField()
    quantity = forms.IntegerField()

    def clean_ticket_type(self):
        data = self.cleaned_data['ticket_type']
        ticket_type = TypeTicket.objects.filter(id=data).exists()
        if not ticket_type:
            raise forms.ValidationError("The type of ticket don't exist")
        return data
