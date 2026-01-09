from django.urls import path
from .views import (
    PromotionListView, AdminPromotionListCreateView, AdminPromotionDetailView,
    DiscountCodeValidateView, AdminDiscountCodeListCreateView, AdminDiscountCodeDetailView,
    AdminBundleDealListCreateView, AdminBundleDealDetailView,
)

app_name = 'promotions'

urlpatterns = [
    # User
    path('', PromotionListView.as_view(), name='promotion_list'),
    path('code/validate/', DiscountCodeValidateView.as_view(), name='discount_code_validate'),

    # Admin
    path('admin/', AdminPromotionListCreateView.as_view(), name='admin_promotion_list_create'),
    path('admin/<int:pk>/', AdminPromotionDetailView.as_view(), name='admin_promotion_detail'),
    path('admin/codes/', AdminDiscountCodeListCreateView.as_view(), name='admin_code_list_create'),
    path('admin/codes/<int:pk>/', AdminDiscountCodeDetailView.as_view(), name='admin_code_detail'),
    path('admin/bundles/', AdminBundleDealListCreateView.as_view(), name='admin_bundle_list_create'),
    path('admin/bundles/<int:pk>/', AdminBundleDealDetailView.as_view(), name='admin_bundle_detail'),
]