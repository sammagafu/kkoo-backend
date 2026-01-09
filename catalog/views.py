from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from .models import Category, Brand, Product, SKU, ProductMedia
from .serializers import (
    CategorySerializer, BrandSerializer, ProductListSerializer,
    ProductDetailSerializer, ProductCreateUpdateSerializer, ProductMediaSerializer,ViewedItemSerializer, RecommendationSerializer
)
from .filters import ProductFilter 


class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]


class BrandListView(generics.ListAPIView):
    queryset = Brand.objects.filter(is_active=True, is_verified=True)
    serializer_class = BrandSerializer
    permission_classes = [permissions.AllowAny]


class ProductListView(generics.ListAPIView):
    """
    Public product list – SQLite compatible
    Uses django-filter + basic Q lookup for search (title, description, brand)
    """
    serializer_class = ProductListSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_class = ProductFilter

    def get_queryset(self):
        qs = Product.objects.filter(
            is_active=True,
            verification_status='approved'
        ).select_related(
            'brand', 'category'
        ).prefetch_related(
            'media', 'skus'
        )

        # Basic keyword search (works on SQLite)
        search_query = self.request.query_params.get('search')
        if search_query:
            qs = qs.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(brand__name__icontains=search_query)
            ).order_by('-created_at')  # Relevance not ranked, but good enough for start

        return qs


class ProductDetailView(generics.RetrieveAPIView):
    queryset = Product.objects.filter(is_active=True, verification_status='approved')
    serializer_class = ProductDetailSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'slug'


class ProductCreateView(generics.CreateAPIView):
    serializer_class = ProductCreateUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        user = self.request.user
        if not hasattr(user, 'seller_profile') or not user.seller_profile.is_core_kyc_complete():
            raise serializers.ValidationError("You must have a verified seller profile to create products.")
        serializer.save(seller=user.seller_profile)


class ProductUpdateView(generics.UpdateAPIView):
    serializer_class = ProductCreateUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Product.objects.filter(seller=self.request.user.seller_profile)


class ProductDeleteView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Product.objects.filter(seller=self.request.user.seller_profile)


# ADMIN VIEWS (unchanged – full governance)
class AdminBrandListView(generics.ListCreateAPIView):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer
    permission_classes = [permissions.IsAdminUser]


class AdminBrandUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer
    permission_classes = [permissions.IsAdminUser]
    lookup_field = 'slug'


class AdminBrandVerifyView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, pk):
        brand = get_object_or_404(Brand, pk=pk)
        action = request.data.get('action')
        if action == 'verify':
            brand.is_verified = True
        elif action == 'unverify':
            brand.is_verified = False
        else:
            return Response({"error": "Invalid action"}, status=status.HTTP_400_BAD_REQUEST)
        brand.save()
        return Response({"message": f"Brand {action}ed", "is_verified": brand.is_verified})


class AdminProductListView(generics.ListAPIView):
    serializer_class = ProductDetailSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        qs = Product.objects.all().select_related(
            'seller__user', 'brand', 'category'
        ).prefetch_related('media', 'skus')
        status = self.request.query_params.get('status')
        seller_phone = self.request.query_params.get('seller')
        if status:
            qs = qs.filter(verification_status=status)
        if seller_phone:
            qs = qs.filter(seller__user__phone_number=seller_phone)
        return qs


class AdminProductVerifyView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        action = request.data.get('action')
        if action == 'approve':
            if product.verification_status == 'approved':
                return Response({"error": "Already approved"}, status=status.HTTP_400_BAD_REQUEST)
            product.verification_status = 'approved'
            product.verified_by = request.user
            product.verified_at = timezone.now()
        elif action == 'reject':
            product.verification_status = 'rejected'
            product.verified_by = request.user
            product.verified_at = timezone.now()
            product.is_active = False
        else:
            return Response({"error": "Invalid action"}, status=status.HTTP_400_BAD_REQUEST)
        product.save()
        return Response({"message": f"Product {action}d", "status": product.verification_status})


class AdminProductDeactivateView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        action = request.data.get('action')
        product.is_active = action == 'activate'
        product.save()
        return Response({"message": f"Product {action}d", "is_active": product.is_active})


class AdminMediaListView(generics.ListAPIView):
    serializer_class = ProductMediaSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        qs = ProductMedia.objects.all()
        product_id = self.request.query_params.get('product')
        is_verified = self.request.query_params.get('is_verified')
        if product_id:
            qs = qs.filter(product__id=product_id)
        if is_verified is not None:
            qs = qs.filter(is_verified=bool(int(is_verified)))
        return qs


class AdminMediaVerifyView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, pk):
        media = get_object_or_404(ProductMedia, pk=pk)
        action = request.data.get('action')
        if action == 'verify':
            media.is_verified = True
        elif action == 'reject':
            media.is_verified = False
            media.delete()
        else:
            return Response({"error": "Invalid action"}, status=status.HTTP_400_BAD_REQUEST)
        media.save()
        return Response({"message": f"Media {action}ed"})


class AdminBulkProductActionView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request):
        action = request.data.get('action')
        product_ids = request.data.get('product_ids', [])
        if not product_ids:
            return Response({"error": "No product IDs provided"}, status=status.HTTP_400_BAD_REQUEST)

        queryset = Product.objects.filter(id__in=product_ids)

        if action == 'approve':
            queryset.update(
                verification_status='approved',
                verified_by=request.user,
                verified_at=timezone.now()
            )
        elif action == 'reject':
            queryset.update(verification_status='rejected', verified_by=request.user, verified_at=timezone.now())
        elif action == 'deactivate':
            queryset.update(is_active=False)
        else:
            return Response({"error": "Invalid action"}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"message": f"{len(product_ids)} products {action}d"})
    

class ViewedItemCreateView(generics.CreateAPIView):
    serializer_class = ViewedItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        product_id = self.request.data.get('product_id')
        product = get_object_or_404(Product, id=product_id, is_active=True, verification_status='approved')
        serializer.save(user=self.request.user, product=product)


class RecommendationView(generics.ListAPIView):
    serializer_class = RecommendationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # Viewed + searched similar: same category/brand
        viewed_categories = ViewedItem.objects.filter(user=user).values_list('product__category', flat=True).distinct()
        viewed_brands = ViewedItem.objects.filter(user=user).values_list('product__brand', flat=True).distinct()
        return Product.objects.filter(
            models.Q(category__in=viewed_categories) | models.Q(brand__in=viewed_brands),
            is_active=True,
            verification_status='approved'
        ).exclude(id__in=ViewedItem.objects.filter(user=user).values_list('product__id', flat=True))  # Exclude viewed