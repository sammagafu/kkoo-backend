from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import User, BuyerProfile, SellerProfile
from .utils import create_test_user, create_test_seller_user


class UserAuthTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = create_test_user("+255712345678")

    def test_otp_request_success(self):
        url = reverse('users:otp_request')
        response = self.client.post(url, {'phone_number': '+255712345678'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('OTP sent', response.data['message'])

    def test_otp_request_invalid_phone(self):
        url = reverse('users:otp_request')
        response = self.client.post(url, {'phone_number': 'invalid'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_profile_authenticated(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('users:user_profile')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['phone_number'], str(self.user.phone_number))

    def test_user_profile_unauthenticated(self):
        url = reverse('users:user_profile')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class SellerProfileTests(APITestCase):
    def setUp(self):
        self.user, self.seller_profile = create_test_seller_user()
        self.client.force_authenticate(user=self.user)

    def test_seller_profile_access(self):
        url = reverse('users:seller_profile')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['kyc_status'], 'verified')


class AdminUserActionTests(APITestCase):
    def setUp(self):
        self.admin = create_test_user(is_staff=True)
        self.client.force_authenticate(user=self.admin)
        self.user = create_test_user("+255987654321")

    def test_ban_user_as_admin(self):
        url = reverse('users:admin_user_action', kwargs={'pk': self.user.pk})
        response = self.client.post(url, {'action': 'ban', 'reason': 'Fraud'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.account_status, 'banned')

    def test_ban_user_as_non_admin(self):
        non_admin = create_test_user()
        self.client.force_authenticate(user=non_admin)
        url = reverse('users:admin_user_action', kwargs={'pk': self.user.pk})
        response = self.client.post(url, {'action': 'ban'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)