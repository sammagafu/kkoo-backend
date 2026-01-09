from django.urls import path
from .views import PaymentWebhookView, AdminPayoutListCreateView, AdminPayoutDetailView

app_name = 'payments'

urlpatterns = [
    path('webhook/', PaymentWebhookView.as_view(), name='payment_webhook'),
    path('admin/payouts/', AdminPayoutListCreateView.as_view(), name='admin_payout_list_create'),
    path('admin/payouts/<int:pk>/', AdminPayoutDetailView.as_view(), name='admin_payout_detail'),
]