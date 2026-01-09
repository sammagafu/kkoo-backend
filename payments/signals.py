from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order

@receiver(post_save, sender=Order)
def release_escrow_on_completion(sender, instance, created, **kwargs):
    if instance.status == 'completed' and not created and not instance.escrow_released:
        instance.escrow_released = True
        instance.save(update_fields=['escrow_released'])
        # Trigger payout batch check