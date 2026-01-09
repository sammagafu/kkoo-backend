from rest_framework import serializers
from .models import Wishlist, Cart, CartItem
from catalog.serializers import ProductDetailSerializer, SKUSerializer


class WishlistSerializer(serializers.ModelSerializer):
    product = ProductDetailSerializer(read_only=True)

    class Meta:
        model = Wishlist
        fields = ['id', 'product', 'added_at']


class CartItemSerializer(serializers.ModelSerializer):
    sku = SKUSerializer(read_only=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ['id', 'sku', 'quantity', 'total_price', 'added_at']

    def get_total_price(self, obj):
        return obj.total_price()


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    discount_info = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ['id', 'items', 'total_amount', 'discount_info', 'created_at', 'updated_at']

    def get_discount_info(self, obj):
        from cart.utils import apply_promotions_to_cart
        return apply_promotions_to_cart(obj)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        discount_data = data.pop('discount_info')
        data.update({
            'original_total': discount_data['original_total'],
            'discount_amount': discount_data['discount_amount'],
            'final_total': discount_data['final_total'],
            'applied_promotions': discount_data['applied_promotions']
        })
        return data