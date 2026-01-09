from rest_framework import serializers
from .models import Review, ReviewPhoto

class ReviewPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewPhoto
        fields = '__all__'
        read_only_fields = ['review', 'uploaded_at']

class ReviewSerializer(serializers.ModelSerializer):
    photos = ReviewPhotoSerializer(many=True, read_only=True)
    buyer_name = serializers.CharField(source='buyer.phone_number', read_only=True)

    class Meta:
        model = Review
        fields = '__all__'
        read_only_fields = ['order', 'buyer', 'product', 'seller', 'is_verified_purchase', 'helpful_votes', 'not_helpful_votes', 'created_at']