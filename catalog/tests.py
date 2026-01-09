from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from users.tests.utils import create_test_user, create_test_seller_user
from .models import Category, Brand, Product


class ProductListViewTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.seller_user, self.seller_profile = create_test_seller_user()
        self.category = Category.objects.create(name="Electronics", slug="electronics")
        self.brand = Brand.objects.create(name="Samsung", slug="samsung", is_verified=True)

        # Approved product
        self.product_approved = Product.objects.create(
            seller=self.seller_profile,
            category=self.category,
            brand=self.brand,
            title="Samsung Galaxy S23",
            description="Flagship phone",
            slug="samsung-galaxy-s23",
            base_price=1500000,
            verification_status='approved',
            is_active=True
        )

        # Pending product (should not appear in public list)
        self.product_pending = Product.objects.create(
            seller=self.seller_profile,
            category=self.category,
            brand=self.brand,
            title="Fake iPhone",
            description="Replica",
            slug="fake-iphone",
            base_price=500000,
            verification_status='pending',
            is_active=True
        )

    def test_public_list_only_shows_approved_products(self):
        url = reverse('catalog:product_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], "Samsung Galaxy S23")

    def test_search_filter_works(self):
        url = reverse('catalog:product_list') + '?search=samsung'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)


class ProductCreateViewTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user, self.seller_profile = create_test_seller_user()
        self.client.force_authenticate(user=self.user)
        self.category = Category.objects.create(name="Electronics", slug="electronics")
        self.brand = Brand.objects.create(name="Apple", slug="apple", is_verified=True)

    def test_create_product_success(self):
        url = reverse('catalog:product_create')
        data = {
            "title": "iPhone 15",
            "description": "Latest model with great camera",
            "slug": "iphone-15",
            "category": self.category.id,
            "brand": self.brand.id,
            "base_price": 2000000,
            "skus": [{"sku_code": "IP15-128", "variant_attributes": {"storage": "128GB"}, "stock_quantity": 10}]
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['verification_status'], 'pending')


class AdminProductVerificationTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = create_test_user(is_staff=True)
        self.client.force_authenticate(user=self.admin)
        _, self.seller_profile = create_test_seller_user()
        self.product = Product.objects.create(
            seller=self.seller_profile,
            title="Test Product",
            slug="test-product",
            base_price=100000,
            verification_status='pending'
        )

    def test_approve_product_as_admin(self):
        url = reverse('catalog:admin_product_verify', kwargs={'pk': self.product.pk})
        response = self.client.post(url, {'action': 'approve'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        self.assertEqual(self.product.verification_status, 'approved')
        self.assertIsNotNone(self.product.verified_at)

    def test_approve_product_as_non_admin(self):
        non_admin = create_test_user()
        self.client.force_authenticate(user=non_admin)
        url = reverse('catalog:admin_product_verify', kwargs={'pk': self.product.pk})
        response = self.client.post(url, {'action': 'approve'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)