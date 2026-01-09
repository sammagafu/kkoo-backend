from django.contrib import admin
from .models import (
    User, Address, BuyerProfile, SellerProfile, SellerKYCDocument
)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("phone_number", "is_seller", "is_verified", "account_status", "last_login")
    search_fields = ("phone_number", "email")
    list_filter = ("is_seller", "is_verified", "account_status")


admin.site.register(Address)
admin.site.register(BuyerProfile)
admin.site.register(SellerProfile)
admin.site.register(SellerKYCDocument)