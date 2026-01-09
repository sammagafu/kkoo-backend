from django.urls import path
from .views import (
    CartDetailView,
    CartItemAddView,
    CartItemUpdateView,
    CartItemRemoveView,
    CartClearView,
)

app_name = 'cart'

urlpatterns = [
    path('', CartDetailView.as_view(), name='cart_detail'),  # GET cart
    path('add/', CartItemAddView.as_view(), name='cart_add_item'),  # POST add
    path('items/<int:pk>/update/', CartItemUpdateView.as_view(), name='cart_update_item'),  # PATCH quantity
    path('items/<int:pk>/remove/', CartItemRemoveView.as_view(), name='cart_remove_item'),  # DELETE item
    path('clear/', CartClearView.as_view(), name='cart_clear'),  # POST clear all
]