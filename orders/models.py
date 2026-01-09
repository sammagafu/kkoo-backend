from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from users.models import User
from catalog.models import SKU


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Payment'),
        ('paid', 'Paid'),
        ('confirmed', 'Seller Confirmed'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('disputed', 'Disputed'),
        ('refunded', 'Refunded'),
    ]

    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='orders')
    order_number = models.CharField(max_length=50, unique=True)
    cart_snapshot = models.JSONField()  # Immutable cart + incentives at checkout
    total_amount = models.DecimalField(max_digits=14, decimal_places=2)  # Final after discounts
    original_amount = models.DecimalField(max_digits=14, decimal_places=2)  # Before discounts
    discount_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    applied_incentives = models.JSONField(default=list)  # Promotions + codes used
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=50, blank=True)
    payment_reference = models.CharField(max_length=100, blank=True)
    escrow_released = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Order {self.order_number}"

    @staticmethod
    def valid_transitions():
        return {
            'pending': ['paid', 'cancelled'],
            'paid': ['confirmed', 'cancelled', 'disputed'],
            'confirmed': ['shipped', 'cancelled', 'disputed'],
            'shipped': ['delivered', 'disputed'],
            'delivered': ['completed', 'disputed'],
            'disputed': ['refunded', 'completed'],
        }

    def clean(self):
        if self.pk:
            old = Order.objects.get(pk=self.pk)
            valid = self.valid_transitions().get(old.status, [])
            if self.status not in valid:
                raise ValidationError(f"Invalid transition: {old.status} → {self.status}")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def release_escrow(self):
        if self.status == 'completed' and not self.escrow_released:
            self.escrow_released = True
            self.save(update_fields=['escrow_released'])


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    sku_snapshot = models.JSONField()
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)


class Delivery(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='delivery')
    estimated_delivery = models.DateTimeField()
    actual_delivery = models.DateTimeField(null=True, blank=True)
    delivery_proof = models.FileField(upload_to='delivery_proof/', blank=True, null=True)


class DisputeEvidence(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='dispute_evidences')
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    file = models.FileField(upload_to='dispute_evidence/')
    description = models.TextField()
    uploaded_at = models.DateTimeField(auto_now_add=True)