from django.contrib import admin
from .models import User,Order,Payement

admin.site.register(User)
admin.site.register(Order)
admin.site.register(Payement)
