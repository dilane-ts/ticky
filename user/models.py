from django.db import models

class User(models.Model):
    ROLES = [
        ('admin', 'admin'),
        ('organizer', 'organizer'),
        ('user', 'user'),
    ]

    name = models.CharField(max_length=128,blank=False)
    email = models.EmailField()
    password = models.CharField(blank=False)
    role = models.CharField(choices=ROLES,max_length=32, default='user')


class Order(models.Model):
    STATUS = [
        ('progress','progress'),
        ('completed','completed')
    ]

    status = models.CharField(choices=STATUS,default='progress')
    user = models.ForeignKey(User,on_delete=models.CASCADE)

class Payement(models.Model):
    operator = models.CharField(blank=False)
    amount = models.DecimalField(max_digits=10,decimal_places=2)
    payement_date = models.DateField(null=False,blank=False)

    order = models.OneToOneField(Order,on_delete=models.CASCADE)