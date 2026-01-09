from django.urls import path
from .views import (
    CategoryListView, BrandListView,
    ProductListView, ProductDetailView,
    ProductCreateView, ProductUpdateView, ProductDeleteView,
    AdminBrandListView, AdminBrandUpdateDeleteView, AdminBrandVerifyView,
    AdminProductListView, AdminProductVerifyView, AdminProductDeactivateView,
    AdminMediaListView, AdminMediaVerifyView,
    AdminBulkProductActionView,
)

app_name = "catalog"

urlpatterns = [
    # Public
    path('categories/', CategoryListView.as_view(), name='category_list'),
    path('brands/', BrandListView.as_view(), name='brand_list'),
    path('products/', ProductListView.as_view(), name='product_list'),
    path('products/<slug:slug>/', ProductDetailView.as_view(), name='product_detail'),

    # Seller
    path('products/create/', ProductCreateView.as_view(), name='product_create'),
    path('products/<int:pk>/update/', ProductUpdateView.as_view(), name='product_update'),
    path('products/<int:pk>/delete/', ProductDeleteView.as_view(), name='product_delete'),

    # Admin
    path('admin/brands/', AdminBrandListView.as_view(), name='admin_brand_list'),
    path('admin/brands/<slug:slug>/', AdminBrandUpdateDeleteView.as_view(), name='admin_brand_detail'),
    path('admin/brands/<int:pk>/verify/', AdminBrandVerifyView.as_view(), name='admin_brand_verify'),
    path('admin/products/', AdminProductListView.as_view(), name='admin_product_list'),
    path('admin/products/<int:pk>/verify/', AdminProductVerifyView.as_view(), name='admin_product_verify'),
    path('admin/products/<int:pk>/deactivate/', AdminProductDeactivateView.as_view(), name='admin_product_deactivate'),
    path('admin/media/', AdminMediaListView.as_view(), name='admin_media_list'),
    path('admin/media/<int:pk>/verify/', AdminMediaVerifyView.as_view(), name='admin_media_verify'),
    path('admin/products/bulk-action/', AdminBulkProductActionView.as_view(), name='admin_bulk_product_action'),
]