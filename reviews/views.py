from rest_framework import generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Review, ReviewPhoto
from .serializers import ReviewSerializer

class ReviewCreateView(APIView):
    """
    POST: Buyer submit review after delivery
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, order_id):
        order = get_object_or_404(
            Order,
            id=order_id,
            user=request.user,
            status='completed'
        )
        if hasattr(order, 'review'):
            return Response({"error": "Review already submitted"}, status=400)

        data = request.data.copy()
        data['order'] = order.id
        data['buyer'] = request.user.id
        data['product'] = order.items.first().product.id
        data['seller'] = order.items.first().product.seller.id

        serializer = ReviewSerializer(data=data)
        if serializer.is_valid():
            review = serializer.save()
            # Handle photos if uploaded
            photos = request.FILES.getlist('photos')
            for photo in photos:
                ReviewPhoto.objects.create(review=review, photo=photo)
            return Response(ReviewSerializer(review).data, status=201)
        return Response(serializer.errors, status=400)


class ReviewListView(generics.ListAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        product_id = self.kwargs.get('product_id')
        return Review.objects.filter(product_id=product_id, is_verified_purchase=True).order_by('-created_at')