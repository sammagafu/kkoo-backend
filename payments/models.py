from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from apps.orders.models import Order
from apps.users.models import SellerProfile, User


class Payment(models.Model):
    """
    Incoming payment – mobile money focus
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    method = models.CharField(max_length=50, choices=[('mpesa', 'M-Pesa'), ('tigo_pesa', 'Tigo Pesa'), ('card', 'Card')])
    reference = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Payment for Order {self.order.order_number} – {self.amount} TZS"

    def save(self, *args, **kwargs):
        if self.status == 'completed':
            self.completed_at = self.completed_at or timezone.now()
            self.order.status = 'paid'
            self.order.save(update_fields=['status'])
        super().save(*args, **kwargs)


class Payout(models.Model):
    """
    Seller payout batch – released after completion
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processed', 'Processed'),
        ('failed', 'Failed'),
    ]

    seller = models.ForeignKey(SellerProfile, on_delete=models.CASCADE, related_name='payouts')
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    method = models.CharField(max_length=50)
    reference = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    orders = models.ManyToManyField(Order, related_name='payouts')
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Payout {self.amount} TZS to {self.seller}"

    def clean(self):
        if self.status == 'processed' and not self.seller.kyc_status == 'verified':
            raise ValidationError("Seller must be verified for payout")

    def save(self, *args, **kwargs):
        self.full_clean()
        if self.status == 'processed':
            self.processed_at = self.processed_at or timezone.now()
        super().save(*args, **kwargs)