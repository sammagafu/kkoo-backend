from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from catalog.models import Product, SKU, Category
from users.models import SellerProfile, User


class Promotion(models.Model):
    PROMOTION_TYPES = [
        ('flash', 'Flash Deal (24h max)'),
        ('timed', 'Time-Based Deal'),
        ('bundle', 'Bundle Deal'),
        ('seller', 'Seller-Specific Deal'),
        ('category', 'Category Deal'),
    ]

    name = models.CharField(max_length=255)
    promotion_type = models.CharField(max_length=20, choices=PROMOTION_TYPES)
    description = models.TextField(blank=True)
    discount_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(1), MaxValueValidator(70)]
    )
    priority = models.PositiveIntegerField(
        default=100,
        help_text="Higher priority wins when multiple promotions match (100 = normal, 200 = high)"
    )
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    min_order_amount = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        help_text="Minimum cart total to apply promotion"
    )
    max_discount_cap = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        help_text="Maximum discount per use (absolute TZS)"
    )
    max_total_burn = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True,
        help_text="Auto-deactivate when total burn reaches this"
    )
    total_burn = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    max_uses = models.PositiveIntegerField(null=True, blank=True)
    uses_count = models.PositiveIntegerField(default=0)
    max_uses_per_user = models.PositiveIntegerField(default=1, help_text="Limit per customer")
    allow_stacking = models.BooleanField(default=False, help_text="Can combine with other promotions?")
    exclude_from_other_promos = models.BooleanField(default=False, help_text="This promo blocks others")
    visibility_boost = models.BooleanField(default=False, help_text="Boost in search/feed for eligible items")
    is_active = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_promotions')
    created_at = models.DateTimeField(auto_now_add=True)

    # Targets
    products = models.ManyToManyField(Product, blank=True, related_name='promotions')
    skus = models.ManyToManyField(SKU, blank=True, related_name='promotions')
    categories = models.ManyToManyField(Category, blank=True, related_name='promotions')
    sellers = models.ManyToManyField(SellerProfile, blank=True, related_name='promotions')

    def __str__(self):
        return f"{self.name} ({self.promotion_type}) – {self.discount_percent}%"

    def clean(self):
        if self.promotion_type == 'flash':
            duration = self.end_datetime - self.start_datetime
            if duration.days > 1 or (duration.days == 1 and duration.seconds > 0):
                raise ValidationError("Flash deals must be 24 hours or less")
        if self.start_datetime >= self.end_datetime:
            raise ValidationError("End datetime must be after start datetime")

    def save(self, *args, **kwargs):
        self.full_clean()
        now = timezone.now()
        within_time = self.start_datetime <= now <= self.end_datetime
        within_uses = self.max_uses is None or self.uses_count < self.max_uses
        within_burn = self.max_total_burn is None or self.total_burn < self.max_total_burn
        self.is_active = within_time and within_uses and within_burn
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-priority', '-created_at']
        indexes = [
            models.Index(fields=['is_active', 'start_datetime', 'end_datetime']),
            models.Index(fields=['priority']),
        ]


class DiscountCode(models.Model):
    code = models.CharField(max_length=50, unique=True)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    max_uses = models.PositiveIntegerField(default=1)
    uses_count = models.PositiveIntegerField(default=0)
    max_uses_per_user = models.PositiveIntegerField(default=1)
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    min_order_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_discount_codes')
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if self.valid_from >= self.valid_until:
            raise ValidationError("Valid until must be after valid from")

    def save(self, *args, **kwargs):
        self.full_clean()
        now = timezone.now()
        self.is_active = self.valid_from <= now <= self.valid_until and self.uses_count < self.max_uses
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.code} – {self.discount_amount or self.discount_percent}% TZS"


class BundleDeal(models.Model):
    promotion = models.OneToOneField(Promotion, on_delete=models.CASCADE, related_name='bundle_detail')
    bundle_skus = models.ManyToManyField(SKU)
    bundle_price = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"Bundle: {self.promotion.name}"