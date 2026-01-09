from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    CustomTokenObtainPairView,
    UserProfileView,
    BuyerProfileView,
    SellerProfileView,
    OTPRequestView,
    AddressListCreateView,
)

app_name = "users"

urlpatterns = [
    # Authentication
    path("login/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("otp/request/", OTPRequestView.as_view(), name="otp_request"),

    # Profiles
    path("me/", UserProfileView.as_view(), name="user_profile"),
    path("buyer/profile/", BuyerProfileView.as_view(), name="buyer_profile"),
    path("seller/profile/", SellerProfileView.as_view(), name="seller_profile"),

    # Addresses
    path("addresses/", AddressListCreateView.as_view(), name="address_list_create"),
]