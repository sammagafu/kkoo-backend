from rest_framework import serializers
from .models import Promotion, DiscountCode, BundleDeal


class PromotionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Promotion
        fields = '__all__'
        read_only_fields = ['created_by', 'created_at', 'is_active', 'uses_count', 'total_burn']

class DiscountCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiscountCode
        fields = '__all__'
        read_only_fields = ['created_by', 'created_at', 'is_active', 'uses_count']

class BundleDealSerializer(serializers.ModelSerializer):
    class Meta:
        model = BundleDeal
        fields = '__all__'