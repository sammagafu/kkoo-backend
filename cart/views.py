from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import Cart, CartItem
from catalog.models import SKU
from .serializers import CartSerializer


class CartDetailView(generics.RetrieveAPIView):
    """
    GET: Pure cart state (no incentives)
    """
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        cart, _ = Cart.objects.get_or_create(user=self.request.user)
        return cart


class CartItemAddView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        sku_id = request.data.get('sku_id')
        quantity = int(request.data.get('quantity', 1))
        if quantity < 1:
            return Response({"error": "Quantity must be at least 1"}, status=400)

        sku = get_object_or_404(
            SKU,
            id=sku_id,
            product__verification_status='approved',
            product__is_active=True,
            is_available=True,
            stock_quantity__gte=quantity
        )

        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            sku=sku,
            defaults={'quantity': quantity}
        )

        if not created:
            new_quantity = cart_item.quantity + quantity
            if new_quantity > sku.stock_quantity:
                return Response({"error": "Not enough stock"}, status=400)
            cart_item.quantity = new_quantity
            cart_item.save()

        cart.updated_at = timezone.now()
        cart.save(update_fields=['updated_at'])

        return Response(CartSerializer(cart).data)


class CartItemUpdateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk):
        quantity = int(request.data.get('quantity'))
        if quantity < 1:
            return Response({"error": "Quantity must be at least 1"}, status=400)

        cart_item = get_object_or_404(CartItem, pk=pk, cart__user=request.user)
        if quantity > cart_item.sku.stock_quantity:
            return Response({"error": "Not enough stock"}, status=400)

        cart_item.quantity = quantity
        cart_item.save()
        cart_item.cart.updated_at = timezone.now()
        cart_item.cart.save(update_fields=['updated_at'])

        return Response(CartSerializer(cart_item.cart).data)


class CartItemRemoveView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return CartItem.objects.filter(cart__user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        cart = instance.cart
        self.perform_destroy(instance)
        cart.updated_at = timezone.now()
        cart.save(update_fields=['updated_at'])
        return Response(CartSerializer(cart).data)


class CartClearView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        cart = get_object_or_404(Cart, user=request.user)
        cart.items.all().delete()
        cart.updated_at = timezone.now()
        cart.save(update_fields=['updated_at'])
        return Response({"message": "Cart cleared", "cart": CartSerializer(cart).data})