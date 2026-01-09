from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from users.models import User
from orders.models import Order
from catalog.models import Product


class Review(models.Model):
    """
    Verified buyer review — trust core
    """
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='review')
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_given')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    seller = models.ForeignKey('users.SellerProfile', on_delete=models.CASCADE, related_name='reviews_received')

    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="1-5 stars"
    )
    title = models.CharField(max_length=100)
    comment = models.TextField()
    is_verified_purchase = models.BooleanField(default=True)

    # FIXED: explicit related_name to avoid clash
    photos = models.ManyToManyField(
        'reviews.ReviewPhoto',
        blank=True,
        related_name='reviews'  # Unique reverse name
    )

    helpful_votes = models.PositiveIntegerField(default=0)
    not_helpful_votes = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_edited = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('order', 'product')

    def __str__(self):
        return f"{self.buyer} → {self.product.title} ({self.rating} stars)"

    def save(self, *args, **kwargs):
        self.is_edited = True if self.pk else False
        super().save(*args, **kwargs)

        # Update seller average rating
        avg = Review.objects.filter(seller=self.seller).aggregate(
            models.Avg('rating')
        )['rating__avg'] or 0
        self.seller.average_rating = round(avg, 2)
        self.seller.save(update_fields=['average_rating'])

        # Recalculate visibility score
        self.seller.calculate_visibility_score()


class ReviewPhoto(models.Model):
    """
    Evidence photos for review
    """
    # FIXED: explicit related_name (optional but clearer)
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name='attached_photos'
    )
    photo = models.ImageField(upload_to='review_photos/%Y/%m/%d/')
    caption = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Photo for review {self.review.id}"