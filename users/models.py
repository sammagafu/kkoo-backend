from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField
from django.core.validators import MinValueValidator, MaxValueValidator
import string
import random
from django.db.models.signals import post_save
from django.dispatch import receiver


class User(AbstractUser):
    """
    Custom user model: phone-first identity for mobile-money-first Africa.
    Overrides groups & user_permissions to prevent reverse accessor clash.
    """
    username = None
    email = models.EmailField(_("email address"), blank=True, null=True)

    phone_number = PhoneNumberField(
        _("phone number"),
        unique=True,
        blank=False,
        null=False,
        help_text=_("E.164 format: +255712345678"),
    )

    language_preference = models.CharField(
        max_length=10, choices=[("en", "English"), ("sw", "Swahili")], default="en"
    )

    is_seller = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)

    date_of_birth = models.DateField(null=True, blank=True)

    # Trust & Fraud Prevention
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    last_login_device = models.CharField(max_length=255, blank=True)
    device_fingerprint_hash = models.CharField(max_length=128, blank=True)

    # Governance
    account_status = models.CharField(
        max_length=20,
        choices=[("active", "Active"), ("suspended", "Suspended"), ("banned", "Banned")],
        default="active"
    )
    banned_reason = models.TextField(blank=True)
    banned_by = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL, related_name="banned_users"
    )

    # Referral & Loyalty
    referral_code = models.CharField(max_length=12, unique=True, blank=True, null=True)
    referred_by = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL, related_name="referred_users"
    )
    loyalty_points_balance = models.PositiveIntegerField(default=0)
    loyalty_points_expiry = models.DateTimeField(null=True, blank=True)
    # === CRITICAL FIX: Override to avoid clash with auth.User ===
    groups = models.ManyToManyField(
        Group,
        related_name="custom_user_set",  # Unique name prevents clash
        related_query_name="user",
        blank=True,
        help_text=_("The groups this user belongs to."),
        verbose_name=_("groups"),
    )

    user_permissions = models.ManyToManyField(
        Permission,
        related_name="custom_user_set",  # Unique name prevents clash
        related_query_name="user",
        blank=True,
        help_text=_("Specific permissions for this user."),
        verbose_name=_("user permissions"),
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "phone_number"
    REQUIRED_FIELDS = []

    def __str__(self):
        return str(self.phone_number)
    
    def redeem_points(self, points_to_redeem, cart_total):
        if points_to_redeem > self.loyalty_points_balance:
            raise ValueError("Insufficient points")
        if points_to_redeem < 1000:
            raise ValueError("Minimum 1000 points")
        max_discount = cart_total * 0.5  # Max 50% off
        discount = min(points_to_redeem, max_discount)
        self.loyalty_points_balance -= discount
        self.save(update_fields=['loyalty_points_balance'])
        return discount
    
    @receiver(post_save, sender=User)
    def generate_referral_code(sender, instance, created, **kwargs):
        if created and not instance.referral_code:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            while User.objects.filter(referral_code=code).exists():
                code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        instance.referral_code = code
        instance.save(update_fields=['referral_code'])

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")
        ordering = ["-created_at"]


class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="addresses")
    street = models.CharField(max_length=255)
    ward = models.CharField(max_length=100, blank=True)
    district = models.CharField(max_length=100)
    region = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default="Tanzania")
    postal_code = models.CharField(max_length=20, blank=True)
    is_default = models.BooleanField(default=False)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.street}, {self.district}"

    class Meta:
        ordering = ["-is_default"]


class BuyerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="buyer_profile")
    preferred_sizes = models.JSONField(default=dict, blank=True)
    style_preferences = models.JSONField(default=list, blank=True)
    preferred_categories = models.JSONField(default=list, blank=True)
    favorite_colors = models.JSONField(default=list, blank=True)
    body_measurements = models.JSONField(default=dict, blank=True)
    default_address = models.ForeignKey(
        Address, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    wishlist_count = models.PositiveIntegerField(default=0)

    notification_preferences = models.JSONField(
        default=dict,
        help_text=_("e.g. {'sms': true, 'push': true, 'whatsapp': false}")
    )
    total_refunds_received = models.PositiveIntegerField(default=0)
    dispute_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Buyer: {self.user.phone_number}"


class SellerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="seller_profile")
    business_name = models.CharField(max_length=255, blank=True)
    tin_number = models.CharField(max_length=50, blank=True)
    business_license_number = models.CharField(max_length=100, blank=True)
    business_license_expiry = models.DateField(null=True, blank=True)
    seller_tier = models.CharField(
        max_length=20,
        choices=[("basic", "Basic"), ("trusted", "Trusted"), ("premium", "Premium")],
        default="basic"
    )
    suspended_until = models.DateField(null=True, blank=True)

    preferred_payout_method = models.CharField(
        max_length=50,
        choices=[("mpesa", "M-Pesa"), ("tigo_pesa", "Tigo Pesa"), ("bank", "Bank Transfer")],
        default="mpesa"
    )
    payout_account_details = models.CharField(max_length=255, blank=True)  # Encrypt in production

    kyc_status = models.CharField(
        max_length=20,
        choices=[("pending", "Pending"), ("verified", "Verified"), ("rejected", "Rejected")],
        default="pending"
    )
    verification_date = models.DateTimeField(null=True, blank=True)
    visibility_score = models.DecimalField(max_digits=5, decimal_places=2, default=50.00)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    total_orders = models.PositiveIntegerField(default=0)
    on_time_delivery_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    total_refunds_issued = models.PositiveIntegerField(default=0)

    def is_core_kyc_complete(self):
        required_docs = self.documents.filter(
            document_type__in=["brela_certificate", "tin_certificate"],
            status="verified"
        ).count()
        return (
            required_docs == 2 and
            bool(self.tin_number) and
            bool(self.business_license_number) and
            (self.business_license_expiry is None or self.business_license_expiry >= timezone.now().date())
        )
    
    def calculate_visibility_score(self):
        on_time = self.on_time_delivery_rate or 0
        accuracy = 100 - (self.total_refunds_issued / max(self.total_orders, 1) * 100)
        rating = self.average_rating * 20
        score = (on_time * 0.5) + (accuracy * 0.3) + (rating * 0.2)
        self.visibility_score = min(max(score, 0), 100)
        self.save(update_fields=['visibility_score'])
        
    def __str__(self):
        return f"Seller: {self.business_name or self.user.phone_number}"


class SellerKYCDocument(models.Model):

    DOCUMENT_TYPES = [
        ("brela_certificate", "BRELA Certificate / Business License"),
        ("tin_certificate", "TIN / Tax Certificate"),
        ("bank_statement", "3-Month Bank Statement"),
        ("other", "Other Supporting Document"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending Review"),
        ("verified", "Verified"),
        ("rejected", "Rejected"),
    ]

    seller_profile = models.ForeignKey(SellerProfile, on_delete=models.CASCADE, related_name="documents")
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    file = models.FileField(upload_to="kyc/%Y/%m/%d/", blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="reviewed_kyc_docs")
    rejection_reason = models.TextField(blank=True, null=True)
    expiry_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.get_document_type_display()} ({self.status})"

    class Meta:
        ordering = ["-submitted_at"]
        unique_together = [("seller_profile", "document_type")]


class LoyaltyRedemption(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='redemptions')
    points_used = models.PositiveIntegerField()
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2)
    order = models.ForeignKey('orders.Order', null=True, blank=True, on_delete=models.SET_NULL)
    redeemed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} redeemed {self.points_used} points"