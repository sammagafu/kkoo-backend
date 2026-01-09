from rest_framework import generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import Promotion, DiscountCode, BundleDeal
from .serializers import PromotionSerializer, DiscountCodeSerializer, BundleDealSerializer


# ========================
# USER VIEWS (READ-ONLY)
# ========================

class PromotionListView(generics.ListAPIView):
    """
    Public endpoint: List only ACTIVE promotions
    """
    serializer_class = PromotionSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        now = timezone.now()
        return Promotion.objects.filter(
            is_active=True,
            start_datetime__lte=now,
            end_datetime__gte=now
        ).order_by('-priority', '-discount_percent')


class DiscountCodeValidateView(APIView):
    """
    POST: Validate discount code
    Body: {"code": "WELCOME500"}
    Returns discount amount if valid
    """
    permission_classes = [permissions.AllowAny]  # Used at checkout

    def post(self, request):
        code_str = request.data.get('code', '').strip().upper()
        if not code_str:
            return Response({"error": "Code required"}, status=400)

        try:
            code = DiscountCode.objects.get(code=code_str, is_active=True)
            return Response({
                "valid": True,
                "discount_amount": float(code.discount_amount),
                "message": "Code valid"
            })
        except DiscountCode.DoesNotExist:
            return Response({"valid": False, "error": "Invalid or expired code"}, status=400)


# ========================
# ADMIN VIEWS (FULL CRUD)
# ========================

class AdminPromotionListCreateView(generics.ListCreateAPIView):
    """
    Admin: List all + Create new promotion
    """
    serializer_class = PromotionSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        return Promotion.objects.all().order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class AdminPromotionDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Admin: Retrieve / Update / Delete single promotion
    """
    serializer_class = PromotionSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        return Promotion.objects.all()


class AdminDiscountCodeListCreateView(generics.ListCreateAPIView):
    """
    Admin: List all + Create new discount code
    """
    serializer_class = DiscountCodeSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        return DiscountCode.objects.all().order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class AdminDiscountCodeDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Admin: Retrieve / Update / Delete single discount code
    """
    serializer_class = DiscountCodeSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        return DiscountCode.objects.all()


class AdminBundleDealListCreateView(generics.ListCreateAPIView):
    """
    Admin: List all + Create bundle deal
    """
    serializer_class = BundleDealSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        return BundleDeal.objects.all()


class AdminBundleDealDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Admin: Retrieve / Update / Delete bundle deal
    """
    serializer_class = BundleDealSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        return BundleDeal.objects.all()