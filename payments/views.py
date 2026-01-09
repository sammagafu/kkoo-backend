from rest_framework import generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import transaction
from .models import Payment, Payout
from .serializers import PaymentSerializer, PayoutSerializer
from orders.models import Order


class PaymentWebhookView(APIView):
    """
    POST: M-Pesa callback – mark payment completed
    """
    permission_classes = [permissions.AllowAny]  # Secure with IP whitelist in production

    def post(self, request):
        # Parse M-Pesa callback data
        transaction_id = request.data.get('transaction_id')
        amount = request.data.get('amount')
        status = request.data.get('status')

        if status != 'success':
            return Response({"error": "Payment failed"}, status=400)

        payment = get_object_or_404(Payment, reference=transaction_id)
        with transaction.atomic():
            payment.status = 'completed'
            payment.save()

        return Response({"message": "Payment confirmed"})


class AdminPayoutListCreateView(generics.ListCreateAPIView):
    serializer_class = PayoutSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        return Payout.objects.all().order_by('-created_at')

    def perform_create(self, serializer):
        seller_id = self.request.data.get('seller_id')
        seller = get_object_or_404(SellerProfile, id=seller_id)
        if not seller.escrow_released_orders().exists():
            raise ValidationError("No completed orders for payout")

        completed_orders = seller.escrow_released_orders()
        amount = completed_orders.aggregate(total=models.Sum('total_amount'))['total'] or 0

        payout = serializer.save(
            seller=seller,
            amount=amount,
            method=seller.preferred_payout_method
        )
        payout.orders.set(completed_orders)
        payout.save()

        # Mark orders as paid out
        completed_orders.update(escrow_released=False)  # Reset or track

class AdminPayoutDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = PayoutSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        return Payout.objects.all()

    def perform_update(self, serializer):
        payout = self.get_object()
        if payout.status == 'processed':
            raise ValidationError("Already processed")
        serializer.save(processed_at=timezone.now(), status='processed')