from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ROLES = [
        ('admin', 'admin'),
        ('organizer', 'organizer'),
        ('user', 'user'),
    ]

    email = models.EmailField()
    password = models.CharField(blank=False)
    phone = models.CharField(unique=True)
    role = models.CharField(choices=ROLES,max_length=32, default='user')

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = ['username', 'email', 'role']

class Order(models.Model):
    STATUS = [
        ('progress','progress'),
        ('completed','completed')
    ]

    status = models.CharField(choices=STATUS,default='progress')
    reference = models.CharField(null=True)
    user = models.ForeignKey(User,on_delete=models.CASCADE)

class Payement(models.Model):
    operator = models.CharField(blank=False)
    amount = models.DecimalField(max_digits=10,decimal_places=2)
    payement_date = models.DateField(null=False,blank=False)

    order = models.OneToOneField(Order,on_delete=models.CASCADE)