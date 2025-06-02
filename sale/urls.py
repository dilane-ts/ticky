from django.urls import path
from .views import index, event_detail, ticket_order, checkout_order

urlpatterns = [
    path('', index, name='home'),
    path('event/<int:pk>/', event_detail, name='event_detail'),
    path('ticket/order/', ticket_order ,name='ticket_order'),
    path('checkout/<int:id>', checkout_order, name='checkout_order')
]
