from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order
from referrals.models import ReferralReward

@receiver(post_save, sender=Order)
def reward_referral(sender, instance, created, **kwargs):
    if instance.status == 'completed' and not created:
        if instance.user.referred_by and not ReferralReward.objects.filter(referrer=instance.user.referred_by, referred=instance.user).exists():
            reward = ReferralReward.objects.create(
                referrer=instance.user.referred_by,
                referred=instance.user,
                order=instance,
                amount=1000
            )
            instance.user.referred_by.loyalty_points_balance += reward.amount
            instance.user.loyalty_points_balance += reward.amount
            instance.user.referred_by.save()
            instance.user.save()