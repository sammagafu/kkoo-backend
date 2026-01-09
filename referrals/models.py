from django.db import models
from users.models import User
from orders.models import Order

class ReferralReward(models.Model):
    referrer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='referral_rewards_given')
    referred = models.ForeignKey(User, on_delete=models.CASCADE, related_name='referral_rewards_received')
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=1000.00)
    rewarded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('referrer', 'referred')