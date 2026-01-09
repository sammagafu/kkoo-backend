from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError
from cart.models import Cart
from cart.utils import apply_loyalty_points
from cart.views import CartDetailView  # Reuse incentive logic
from .models import Order, OrderItem, Delivery
from .serializers import OrderListSerializer, OrderDetailSerializer


class OrderListView(generics.ListAPIView):
    serializer_class = OrderListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by('-created_at')


class OrderDetailView(generics.RetrieveAPIView):
    serializer_class = OrderDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Order.objects.all()
        return Order.objects.filter(user=self.request.user)


class OrderCreateView(APIView):
    """
    POST: Full checkout — promotion + discount code + loyalty points
    Body: {"discount_code": "WELCOME500", "use_loyalty_points": 2000}
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        discount_code = request.data.get('discount_code', '').strip()
        points_to_use = int(request.data.get('use_loyalty_points', 0))

        cart = get_object_or_404(Cart, user=request.user)
        if not cart.items.exists():
            return Response({"error": "Cart is empty"}, status=status.HTTP_400_BAD_REQUEST)

        # Re-check stock before checkout
        for item in cart.items.all():
            if item.quantity > item.sku.stock_quantity:
                return Response({"error": f"Not enough stock for {item.sku.sku_code}"}, status=400)

        # Apply promotion + discount code
        cart_view = CartDetailView()
        base_incentives = cart_view.apply_promotion_and_code(cart, discount_code)

        # Apply loyalty points
        loyalty_discount = 0
        loyalty_applied = []
        if points_to_use > 0:
            try:
                loyalty_result = apply_loyalty_points(cart, points_to_use)
                loyalty_discount = loyalty_result['discount_amount']
                loyalty_applied = [{'type': 'loyalty', 'amount': loyalty_discount}]
            except ValidationError as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        final_total = base_incentives['final_total'] - loyalty_discount
        if final_total < 0:
            final_total = 0

        with transaction.atomic():
            # Build immutable snapshot
            order_items_data = []
            for item in cart.items.all():
                price = item.sku.price_override or item.sku.product.base_price
                order_items_data.append({
                    'sku_snapshot': {
                        'sku_code': item.sku.sku_code,
                        'variant_attributes': item.sku.variant_attributes,
                        'product_title': item.sku.product.title,
                        'brand': item.sku.product.brand.name if item.sku.product.brand else '',
                        'base_price': float(price),
                    },
                    'quantity': item.quantity,
                    'unit_price': float(price),
                    'total_price': float(price * item.quantity),
                })

            all_applied = base_incentives['applied_incentives'] + loyalty_applied

            order = Order.objects.create(
                user=request.user,
                order_number=f"KK{timezone.now().strftime('%Y%m%d%H%M%S')}{request.user.id}",
                original_amount=base_incentives['original_total'],
                discount_amount=base_incentives['total_discount'] + loyalty_discount,
                total_amount=final_total,
                applied_incentives=all_applied,
                status='pending',
                cart_snapshot={
                    'items': order_items_data,
                    'incentives': all_applied,
                    'original_total': base_incentives['original_total'],
                    'final_total': final_total
                }
            )

            for data in order_items_data:
                OrderItem.objects.create(order=order, **data)

            Delivery.objects.create(order=order, estimated_delivery=timezone.now() + timezone.timedelta(days=3))

            # Clear cart
            cart.items.all().delete()
            cart.updated_at = timezone.now()
            cart.save(update_fields=['updated_at'])

        return Response(OrderDetailSerializer(order).data, status=status.HTTP_201_CREATED)


class OrderPaymentUpdateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk, user=request.user)
        if order.status != 'pending':
            return Response({"error": "Order not pending payment"}, status=status.HTTP_400_BAD_REQUEST)

        payment_ref = request.data.get('payment_reference')
        order.status = 'paid'
        order.payment_reference = payment_ref
        order.paid_at = timezone.now()
        order.save()

        return Response({"message": "Payment recorded", "status": order.status})


class OrderStatusUpdateView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        new_status = request.data.get('status')

        valid_transitions = {
            'paid': ['confirmed', 'cancelled'],
            'confirmed': ['shipped'],
            'shipped': ['delivered'],
            'delivered': ['completed'],
        }

        if order.status not in valid_transitions or new_status not in valid_transitions[order.status]:
            return Response({"error": "Invalid status transition"}, status=status.HTTP_400_BAD_REQUEST)

        order.status = new_status
        if new_status == 'delivered':
            order.delivered_at = timezone.now()
        elif new_status == 'completed':
            order.completed_at = timezone.now()
            order.escrow_released = True
        order.save()

        return Response({"message": f"Order {new_status}", "status": order.status})


class OrderCancelView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk, user=request.user)
        if order.status not in ['pending', 'paid', 'confirmed']:
            return Response({"error": "Cannot cancel at this stage"}, status=status.HTTP_400_BAD_REQUEST)

        order.status = 'cancelled'
        order.save()

        return Response({"message": "Order cancelled", "status": order.status})


class OrderDeliveryProofUploadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        delivery = get_object_or_404(Delivery, order=order)

        proof_file = request.FILES.get('proof')
        if not proof_file:
            return Response({"error": "Proof file required"}, status=status.HTTP_400_BAD_REQUEST)

        delivery.delivery_proof = proof_file
        delivery.actual_delivery = timezone.now()
        delivery.status = 'delivered'
        delivery.save()

        order.status = 'delivered'
        order.delivered_at = timezone.now()
        order.save()

        return Response({"message": "Delivery confirmed with proof"})


class AdminOrderRefundView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        if order.status in ['completed', 'refunded']:
            return Response({"error": "Cannot refund at this stage"}, status=status.HTTP_400_BAD_REQUEST)

        order.status = 'refunded'
        order.save()

        return Response({"message": "Refund processed", "status": order.status})