from django.db.models import Q
from .models import Product, ViewedItem

def get_recommendations(user, limit=12):
    viewed = ViewedItem.objects.filter(user=user).values_list('product__category', 'product__brand')
    categories = [v[0] for v in viewed if v[0]]
    brands = [v[1] for v in viewed if v[1]]

    if not categories and not brands:
        return Product.objects.filter(verification_status='approved', is_active=True)[:limit]

    recommended = Product.objects.filter(
        Q(category__in=categories) | Q(brand__in=brands),
        verification_status='approved',
        is_active=True
    ).exclude(viewed_items__user=user).distinct()[:limit]

    return recommended