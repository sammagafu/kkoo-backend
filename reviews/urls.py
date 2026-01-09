from django.urls import path
from .views import ReviewCreateView, ReviewListView

app_name = 'reviews'

urlpatterns = [
    path('order/<int:order_id>/submit/', ReviewCreateView.as_view(), name='review_submit'),
    path('product/<int:product_id>/', ReviewListView.as_view(), name='review_list'),
]