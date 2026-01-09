from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework_simplejwt.views import TokenObtainPairView
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import User, BuyerProfile, SellerProfile, Address, SellerKYCDocument
from .serializers import (
    UserSerializer, BuyerProfileSerializer, SellerProfileSerializer,
    AddressSerializer, SellerKYCDocumentSerializer, CustomTokenObtainPairSerializer
)
from phonenumber_field.phonenumber import PhoneNumber


# Authentication
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class OTPRequestView(generics.GenericAPIView):
    """Request OTP for login (no password fallback)"""
    def post(self, request):
        phone_str = request.data.get("phone_number")
        if not phone_str:
            return Response({"error": "Phone number required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            phone = PhoneNumber.from_string(phone_str)
            if not phone.is_valid():
                raise ValueError("Invalid phone number format")
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(phone_number=phone)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        # TODO: Integrate Africa's Talking / Twilio to send OTP
        # send_otp(user.phone_number.as_e164)
        return Response({"message": f"OTP sent to {phone.as_e164}"}, status=status.HTTP_200_OK)


class OTPVerifyView(generics.GenericAPIView):
    """Verify OTP and return JWT tokens"""
    def post(self, request):
        phone_str = request.data.get("phone_number")
        code = request.data.get("otp_code")

        if not phone_str or not code:
            return Response({"error": "Phone and OTP code required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            phone = PhoneNumber.from_string(phone_str)
            user = User.objects.get(phone_number=phone)
        except (User.DoesNotExist, ValueError):
            return Response({"error": "Invalid user or phone"}, status=status.HTTP_404_NOT_FOUND)

        # TODO: Verify OTP code with your backend
        # if not verify_otp(user, code):
        #     return Response({"error": "Invalid OTP"}, status=400)

        # For demo: assume valid
        token = CustomTokenObtainPairSerializer.get_token(user)
        return Response({
            "refresh": str(token),
            "access": str(token.access_token),
            "user": UserSerializer(user).data
        })


# User & Profile Views
class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class BuyerProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = BuyerProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        profile, _ = BuyerProfile.objects.get_or_create(user=self.request.user)
        return profile


class SellerProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = SellerProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        profile, created = SellerProfile.objects.get_or_create(user=self.request.user)
        if created:
            self.request.user.is_seller = True
            self.request.user.save(update_fields=['is_seller'])
        return profile


class AddressListCreateView(generics.ListCreateAPIView):
    serializer_class = AddressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.request.user.addresses.all()

    def perform_create(self, serializer):
        addresses = self.request.user.addresses.all()
        is_default = not addresses.exists()
        serializer.save(user=self.request.user, is_default=is_default)


class AddressDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AddressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.request.user.addresses.all()


# ADMIN VIEWS
class UserListAdminView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        qs = super().get_queryset()
        status = self.request.query_params.get('status')
        is_seller = self.request.query_params.get('is_seller')
        if status:
            qs = qs.filter(account_status=status)
        if is_seller is not None:
            qs = qs.filter(is_seller=bool(int(is_seller)))
        return qs


class UserActionAdminView(generics.GenericAPIView):
    permission_classes = [IsAdminUser]

    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        action = request.data.get('action')  # 'ban', 'suspend', 'activate'
        reason = request.data.get('reason', '')

        if action not in ['ban', 'suspend', 'activate']:
            return Response({"error": "Invalid action"}, status=status.HTTP_400_BAD_REQUEST)

        if action == 'ban' and not request.user.is_superuser:
            return Response({"error": "Superadmin required for permanent ban"}, status=status.HTTP_403_FORBIDDEN)

        user.account_status = 'banned' if action == 'ban' else 'suspended' if action == 'suspend' else 'active'
        user.banned_reason = reason if action != 'activate' else ''
        user.banned_by = request.user if action != 'activate' else None
        user.save()

        return Response({"message": f"User {action}d", "status": user.account_status})


class SellerListAdminView(generics.ListAPIView):
    queryset = SellerProfile.objects.all()
    serializer_class = SellerProfileSerializer
    permission_classes = [IsAdminUser]


class SellerApproveAdminView(generics.GenericAPIView):
    permission_classes = [IsAdminUser]

    def post(self, request, pk):
        profile = get_object_or_404(SellerProfile, pk=pk)
        if profile.kyc_status == "verified":
            return Response({"error": "Already verified"}, status=status.HTTP_400_BAD_REQUEST)

        if not profile.is_core_kyc_complete():
            return Response({"error": "Core KYC not complete"}, status=status.HTTP_400_BAD_REQUEST)

        profile.kyc_status = "verified"
        profile.verification_date = timezone.now()
        profile.user.is_verified = True
        profile.user.save(update_fields=['is_verified'])
        profile.save()

        return Response({"message": "Seller approved"})


class SellerRejectAdminView(generics.GenericAPIView):
    permission_classes = [IsAdminUser]

    def post(self, request, pk):
        profile = get_object_or_404(SellerProfile, pk=pk)
        reason = request.data.get('reason', '')

        profile.kyc_status = "rejected"
        profile.verification_date = None
        profile.save()

        profile.documents.filter(status="pending").update(status="rejected", rejection_reason=reason)

        return Response({"message": "Seller rejected", "reason": reason})


class SellerKYCDocumentReviewAdminView(generics.GenericAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = SellerKYCDocumentSerializer

    def post(self, request, pk):
        doc = get_object_or_404(SellerKYCDocument, pk=pk)
        action = request.data.get('action')  # 'verify' / 'reject'
        reason = request.data.get('reason', '')

        if action not in ['verify', 'reject']:
            return Response({"error": "Invalid action"}, status=status.HTTP_400_BAD_REQUEST)

        doc.status = "verified" if action == 'verify' else "rejected"
        doc.reviewed_at = timezone.now()
        doc.reviewed_by = request.user
        doc.rejection_reason = reason if action == 'reject' else ""
        doc.save()

        seller = doc.seller_profile
        if seller.is_core_kyc_complete() and seller.kyc_status != "verified":
            seller.kyc_status = "verified"
            seller.verification_date = timezone.now()
            seller.user.is_verified = True
            seller.user.save()
            seller.save()

        return Response({"message": f"Document {action}ed"})