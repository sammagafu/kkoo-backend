from django.urls import path
from .views import (
    OrderListView, OrderDetailView, OrderCreateView,
    OrderPaymentUpdateView, OrderStatusUpdateView,
    OrderCancelView, OrderDeliveryProofUploadView,
    AdminOrderRefundView
)

app_name = 'orders'

urlpatterns = [
    path('', OrderListView.as_view(), name='order_list'),
    path('<int:pk>/', OrderDetailView.as_view(), name='order_detail'),
    path('create/', OrderCreateView.as_view(), name='order_create'),
    path('<int:pk>/pay/', OrderPaymentUpdateView.as_view(), name='order_pay'),
    path('<int:pk>/status/', OrderStatusUpdateView.as_view(), name='order_status_update'),
    path('<int:pk>/cancel/', OrderCancelView.as_view(), name='order_cancel'),
    path('<int:pk>/delivery-proof/', OrderDeliveryProofUploadView.as_view(), name='delivery_proof'),
    path('admin/<int:pk>/refund/', AdminOrderRefundView.as_view(), name='admin_refund'),
]