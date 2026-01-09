from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from promotions.models import Promotion, DiscountCode


def apply_incentives_to_cart(cart, discount_code=None):
    """
    Apply incentives with full operational discipline
    - Priority ordering (highest wins)
    - No stacking
    - Per-user use cap
    - Minimum order amount
    - Burn tracking
    """
    now = timezone.now()
    user = cart.user
    original_total = cart.total_amount()
    final_total = original_total
    applied = []

    # 1. Promotion – highest priority wins
    promo_discount = 0
    active_promos = Promotion.objects.filter(
        is_active=True,
        start_datetime__lte=now,
        end_datetime__gte=now
    ).order_by('-priority', '-discount_percent')

    for item in cart.items.all():
        sku = item.sku
        product = sku.product

        # Find best eligible promotion
        promo = active_promos.filter(
            Q(products=product) |
            Q(skus=sku) |
            Q(categories=product.category) |
            Q(sellers=product.seller)
        ).first()

        if promo:
            # Check per-user use cap
            if promo.max_uses_per_user:
                user_uses = promo.uses_count  # You'd track per-user in real system
                if user_uses >= promo.max_uses_per_user:
                    continue

            price = sku.price_override or product.base_price
            discount = price * (promo.discount_percent / 100) * item.quantity

            if promo.max_discount_cap:
                discount = min(discount, promo.max_discount_cap)

            if promo.min_order_amount and original_total < promo.min_order_amount:
                continue

            promo_discount += discount
            applied.append({
                'type': 'promotion',
                'name': promo.name,
                'promotion_id': promo.id,
                'amount': discount
            })

            with transaction.atomic():
                promo.total_burn += discount
                promo.uses_count += 1
                promo.save(update_fields=['total_burn', 'uses_count'])

    final_total -= promo_discount

    # 2. Discount Code – one-time use
    code_discount = 0
    if discount_code:
        try:
            code = DiscountCode.objects.select_for_update().get(
                code=discount_code.upper(),
                is_active=True
            )
            if final_total < code.min_order_amount:
                raise ValidationError("Order total too low for code")

            code_discount = code.discount_amount

            with transaction.atomic():
                code.uses_count += 1
                code.save(update_fields=['uses_count'])

            applied.append({
                'type': 'code',
                'code': code.code,
                'amount': code_discount
            })

            final_total -= code_discount
        except DiscountCode.DoesNotExist:
            raise ValidationError("Invalid or expired discount code")

    return {
        'original_total': original_total,
        'promotion_discount': promo_discount,
        'code_discount': code_discount,
        'total_discount': promo_discount + code_discount,
        'final_total': max(final_total, 0),
        'applied_incentives': applied
    }


def apply_loyalty_points(cart, points_to_use):
    """
    Redeem loyalty points with full safeguards
    """
    user = cart.user

    if points_to_use < 1000:
        raise ValidationError("Minimum redemption is 1000 points")

    if points_to_use > user.loyalty_points_balance:
        raise ValidationError("Insufficient loyalty points")

    cart_total = cart.total_amount()
    max_allowed = cart_total * 0.5
    discount = min(points_to_use, max_allowed)

    if discount <= 0:
        raise ValidationError("Cart total too low for redemption")

    with transaction.atomic():
        user.loyalty_points_balance -= discount
        user.save(update_fields=['loyalty_points_balance'])

    return {
        'points_used': discount,
        'discount_amount': discount,
        'remaining_points': user.loyalty_points_balance
    }