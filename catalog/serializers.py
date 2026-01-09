from rest_framework import serializers
from .models import Category, Brand, Product, SKU, ProductMedia, ProductSpecification,ViewedItem


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'parent', 'path', 'is_active']


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ['id', 'name', 'slug', 'logo_url', 'is_verified', 'country_of_origin']
        read_only_fields = ['is_verified']


class ProductMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductMedia
        fields = ['id', 'media_type', 'file_url', 'caption', 'is_primary', 'is_verified', 'uploaded_at']
        read_only_fields = ['is_verified', 'uploaded_at']


class SKUSerializer(serializers.ModelSerializer):
    variant_attributes = serializers.JSONField()

    class Meta:
        model = SKU
        fields = ['id', 'sku_code', 'variant_attributes', 'stock_quantity', 'price_override', 'is_available']
        read_only_fields = ['is_available']


class ProductSpecificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductSpecification
        fields = ['id', 'specs']


class ProductListSerializer(serializers.ModelSerializer):
    brand = BrandSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    primary_media = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'title', 'slug', 'base_price', 'discount_price',
            'brand', 'category', 'verification_status', 'is_active',
            'created_at', 'primary_media'
        ]

    def get_primary_media(self, obj):
        primary = obj.media.filter(is_primary=True).first()
        return ProductMediaSerializer(primary).data if primary else None


class ProductDetailSerializer(serializers.ModelSerializer):
    brand = BrandSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    media = ProductMediaSerializer(many=True, read_only=True)
    skus = SKUSerializer(many=True, read_only=True)
    specification = ProductSpecificationSerializer(read_only=True)

    class Meta:
        model = Product
        fields = '__all__'
        read_only_fields = ['seller', 'verification_status', 'verified_by', 'verified_at', 'created_at', 'updated_at']


class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    skus = SKUSerializer(many=True, required=False)
    media = ProductMediaSerializer(many=True, required=False, read_only=True)
    specification = ProductSpecificationSerializer(required=False)

    class Meta:
        model = Product
        fields = [
            'title', 'description', 'slug', 'category', 'brand',
            'base_price', 'discount_price', 'weight_kg', 'dimensions',
            'skus', 'media', 'specification'
        ]
        read_only_fields = ['seller']

    def validate(self, data):
        if len(data.get('description', '')) < 200:
            raise serializers.ValidationError("Description must be at least 200 characters.")
        if not data.get('skus'):
            raise serializers.ValidationError("At least one SKU is required.")
        return data

    def create(self, validated_data):
        skus_data = validated_data.pop('skus', [])
        specification_data = validated_data.pop('specification', None)

        product = Product.objects.create(**validated_data, seller=self.context['request'].user.seller_profile)
        product.verification_status = 'pending'
        product.save(update_fields=['verification_status'])

        for sku_data in skus_data:
            SKU.objects.create(product=product, **sku_data)

        if specification_data:
            ProductSpecification.objects.create(product=product, **specification_data)

        return product
    
class ViewedItemSerializer(serializers.ModelSerializer):
    product = ProductDetailSerializer(read_only=True)

    class Meta:
        model = ViewedItem
        fields = ['id', 'product', 'viewed_at', 'search_query']


class RecommendationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'title', 'slug', 'base_price', 'brand', 'category']  # Simplified