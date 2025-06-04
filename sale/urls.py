from django.urls import path
from . import views

urlpatterns = [
    path('',  views.index, name='home'),
    path('event/<int:pk>/<str:slug>',  views.event_detail, name='event_detail'),
    path('ticket/order/',  views.ticket_order ,name='ticket_order'),
    path('order/<int:id>/',  views.order_page, name='order_detail'),
    path('payment/success/',  views.payment_sucess, name="payment_sucess"),
    path('ticket/validate/<str:identifier>', views.validate_ticket ,name="ticket_validate"),
    path('order/download/<int:order_id>',  views.download_ticket ,name="download_order"),
     path('webhooks/notchpay/', views.notchpay_webhook, name='notchpay_webhook'),
]
