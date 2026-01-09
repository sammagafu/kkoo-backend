from rest_framework import serializers
from .models import Order, OrderItem, Delivery, DisputeEvidence


class OrderItemSerializer(serializers.ModelSerializer):
    """
    Immutable line item – snapshot at checkout
    """
    class Meta:
        model = OrderItem
        fields = '__all__'
        read_only_fields = ['order', 'sku_snapshot', 'quantity', 'unit_price', 'total_price']


class DeliverySerializer(serializers.ModelSerializer):
    """
    Delivery proof & timestamps – evidence layer
    """
    class Meta:
        model = Delivery
        fields = '__all__'
        read_only_fields = ['order', 'estimated_delivery', 'actual_delivery']


class DisputeEvidenceSerializer(serializers.ModelSerializer):
    """
    Dispute evidence – audit trail for responsibility
    """
    class Meta:
        model = DisputeEvidence
        fields = '__all__'
        read_only_fields = ['order', 'uploaded_by', 'uploaded_at']


class OrderListSerializer(serializers.ModelSerializer):
    """
    Buyer order list – minimal, fast
    """
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'total_amount', 'status',
            'created_at', 'paid_at', 'delivered_at'
        ]
        read_only_fields = fields


class OrderDetailSerializer(serializers.ModelSerializer):
    """
    Full order detail – nested items, delivery, dispute evidence
    """
    items = OrderItemSerializer(many=True, read_only=True)
    delivery = DeliverySerializer(read_only=True)
    dispute_evidences = DisputeEvidenceSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = [
            'user', 'order_number', 'cart_snapshot', 'total_amount',
            'status', 'payment_method', 'payment_reference',
            'escrow_released', 'created_at', 'paid_at',
            'delivered_at', 'completed_at'
        ]


class OrderCreateSerializer(serializers.Serializer):
    """
    Checkout serializer – no model, just validation
    """
    # No fields needed – cart snapshot handled in view
    def create(self, validated_data):
        # Handled in OrderCreateView
        pass

    def update(self, instance, validated_data):
        pass