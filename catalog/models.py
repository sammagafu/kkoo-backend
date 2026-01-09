from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from django.utils import timezone
from users.models import SellerProfile, User  # Top-level import (adjust if needed)


class Category(models.Model):
    """
    Hierarchical categories (e.g., Electronics > Phones > Smartphones)
    """
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='children')
    path = models.CharField(max_length=500, blank=True, editable=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.parent:
            self.path = f"{self.parent.path}{self.slug}/"
        else:
            self.path = f"/{self.slug}/"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = _("categories")
        ordering = ['name']
        indexes = [
            models.Index(fields=['path']),
            models.Index(fields=['parent', 'is_active']),
        ]


class Brand(models.Model):
    """
    Centralized, admin-controlled brands for trust and filtering.
    """
    name = models.CharField(max_length=150, unique=True)
    slug = models.SlugField(max_length=170, unique=True)
    logo = models.ImageField(upload_to='brands/', blank=True, null=True)
    logo_url = models.URLField(blank=True, null=True)
    description = models.TextField(blank=True)
    country_of_origin = models.CharField(max_length=100, blank=True)
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['name', 'slug']),
            models.Index(fields=['is_verified', 'is_active']),
        ]


class Product(models.Model):
    """
    Core product – supports any category.
    """
    seller = models.ForeignKey(SellerProfile, on_delete=models.CASCADE, related_name='products')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='products')
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    title = models.CharField(max_length=255)
    description = models.TextField()
    slug = models.SlugField(max_length=255, unique=True)
    base_price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    discount_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    weight_kg = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    dimensions = models.CharField(max_length=100, blank=True)
    verification_status = models.CharField(
        max_length=20,
        choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected'), ('flagged', 'Flagged')],
        default='pending'
    )
    verified_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='verified_products')
    verified_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['seller', 'is_active', 'verification_status']),
            models.Index(fields=['category', 'is_active', 'created_at']),
            models.Index(fields=['brand', 'is_active', 'verification_status']),
            models.Index(fields=['slug']),
            models.Index(fields=['verification_status', 'created_at']),
        ]
        # Django 6.0 syntax: condition= (not check=)
        constraints = [
            models.CheckConstraint(
                condition=models.Q(base_price__gte=0),
                name='base_price_non_negative'
            ),
        ]


class SKU(models.Model):
    """
    Product variants (color, size, storage, pack size, etc.)
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='skus')
    sku_code = models.CharField(max_length=50, unique=True)
    variant_attributes = models.JSONField(default=dict)
    stock_quantity = models.PositiveIntegerField(default=0)
    price_override = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.product.title} - {self.sku_code}"

    class Meta:
        unique_together = [('product', 'sku_code')]
        indexes = [
            models.Index(fields=['product', 'is_available']),
        ]


class ProductMedia(models.Model):
    MEDIA_TYPES = [
        ('photo', 'Photo'),
        ('video', 'Video'),
        ('document', 'Document/PDF'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='media')
    file = models.FileField(upload_to='products/%Y/%m/%d/')
    file_url = models.URLField(blank=True, null=True)
    media_type = models.CharField(max_length=20, choices=MEDIA_TYPES, default='photo')
    is_verified = models.BooleanField(default=False)
    is_primary = models.BooleanField(default=False)
    caption = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.title} - {self.media_type}"

    class Meta:
        ordering = ['-is_primary', '-uploaded_at']
        indexes = [models.Index(fields=['product', 'is_primary', 'is_verified'])]


class ProductSpecification(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='specification')
    specs = models.JSONField(default=dict)

    def __str__(self):
        return f"Specs for {self.product.title}"


class StockSnapshot(models.Model):
    sku = models.ForeignKey(SKU, on_delete=models.CASCADE, related_name='snapshots')
    quantity = models.PositiveIntegerField()
    snapshot_at = models.DateTimeField(auto_now_add=True)
    reason = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['-snapshot_at']

class ViewedItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='viewed_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    viewed_at = models.DateTimeField(auto_now_add=True)
    search_query = models.CharField(max_length=255, blank=True)  # Optional: tie to search

    class Meta:
        unique_together = ('user', 'product')
        ordering = ['-viewed_at']

    def __str__(self):
        return f"{self.user} viewed {self.product.title}"