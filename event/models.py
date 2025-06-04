from django.db import models
from user.models import Order
from django.utils.text import slugify

class Event(models.Model):

    STATUS = [
        ('draft','draft'),
        ('published','published'),
        ('finished','finished')
    ]

    name = models.CharField(blank=False)
    description = models.TextField()
    location = models.CharField()
    time_start = models.DateField()
    time_end = models.DateField()
    image = models.ImageField(upload_to='images/')
    status = models.CharField(choices=STATUS, default='draft')
    slug = models.SlugField(unique=True, blank=True)
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class TypeTicket(models.Model):
    name = models.CharField()
    description = models.CharField(max_length=512)
    price = models.DecimalField(max_digits=10,decimal_places=2)
    quota = models.IntegerField()

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='type_tickets')

class Ticket(models.Model):

    STATUS = [
        ('notpay','notpay'),
        ('pay', 'pay'),
        ('used', 'used')
    ]

    identifier = models.CharField()
    status = models.CharField(choices=STATUS,default='notpay')
    order = models.ForeignKey(Order,on_delete=models.SET_NULL,null=True)
    type = models.ForeignKey(TypeTicket,on_delete=models.CASCADE)
