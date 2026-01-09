from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import User, BuyerProfile, SellerProfile, Address, SellerKYCDocument


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id", "phone_number", "email", "language_preference",
            "is_seller", "is_verified", "date_of_birth",
            "account_status", "referral_code", "loyalty_points_balance",
            "created_at", "last_login"
        ]
        read_only_fields = ["id", "created_at", "last_login", "account_status"]


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = "__all__"
        read_only_fields = ["user"]


class BuyerProfileSerializer(serializers.ModelSerializer):
    default_address = AddressSerializer(read_only=True)

    class Meta:
        model = BuyerProfile
        fields = "__all__"
        read_only_fields = ["user", "wishlist_count", "total_refunds_received", "dispute_count"]


class SellerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = SellerProfile
        fields = "__all__"
        read_only_fields = ["user", "kyc_status", "verification_date", "seller_tier", "suspended_until"]


class SellerKYCDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SellerKYCDocument
        fields = "__all__"
        read_only_fields = ["status", "reviewed_at", "reviewed_by", "rejection_reason"]


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["phone_number"] = str(user.phone_number)
        token["is_seller"] = user.is_seller
        token["is_verified"] = user.is_verified
        token["account_status"] = user.account_status
        return token