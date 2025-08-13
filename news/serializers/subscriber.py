# news/serializers/subscriber.py
from rest_framework import serializers
from news.models import NewsSubscriber
from core.serializers import UserSerializer
from news.serializers.category import NewsCategorySerializer


class NewsSubscriberSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    category = NewsCategorySerializer(read_only=True)
    subscribed_to = serializers.SerializerMethodField()
    is_category_subscription = serializers.BooleanField(read_only=True)
    is_author_subscription = serializers.BooleanField(read_only=True)

    class Meta:
        model = NewsSubscriber
        fields = [
            'id', 'user', 'category', 'author',
            'subscribed_at', 'source',
            'subscribed_to', 'is_category_subscription', 'is_author_subscription'
        ]
        read_only_fields = fields

    def get_subscribed_to(self, obj):
        if obj.category:
            return f"Category: {obj.category.name}"
        elif obj.author:
            return f"Author: {obj.author.get_full_name()}"
        return None

class NewsSubscriberCreateSerializer(serializers.ModelSerializer):
    category_id = serializers.PrimaryKeyRelatedField(
        source='category',
        queryset=NewsSubscriber._meta.get_field('category').related_model.objects.all(),
        required=False
    )
    author_id = serializers.PrimaryKeyRelatedField(
        source='author',
        queryset=NewsSubscriber._meta.get_field('author').related_model.objects.all(),
        required=False
    )

    class Meta:
        model = NewsSubscriber
        fields = ['category_id', 'author_id', 'source']

    def validate(self, attrs):
        user = self.context['request'].user
        category = attrs.get('category')
        author = attrs.get('author')

        if not category and not author:
            raise serializers.ValidationError("You must subscribe to a category or an author.")

        if category and author:
            raise serializers.ValidationError("You can only subscribe to one: category or author.")

        if NewsSubscriber.objects.filter(user=user, category=category, author=author).exists():
            raise serializers.ValidationError("You are already subscribed.")

        return attrs

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return NewsSubscriber.objects.create(**validated_data)

class NewsUnsubscribeSerializer(serializers.Serializer):
    category_id = serializers.IntegerField(required=False)
    author_id = serializers.IntegerField(required=False)

    def validate(self, attrs):
        user = self.context['request'].user
        category_id = attrs.get('category_id')
        author_id = attrs.get('author_id')

        if not category_id and not author_id:
            raise serializers.ValidationError("Provide either a category or author to unsubscribe from.")

        qs = NewsSubscriber.objects.filter(user=user)
        if category_id:
            qs = qs.filter(category_id=category_id)
        elif author_id:
            qs = qs.filter(author_id=author_id)

        if not qs.exists():
            raise serializers.ValidationError("You are not subscribed to this target.")

        attrs['subscription_qs'] = qs
        return attrs

    def save(self, **kwargs):
        self.validated_data['subscription_qs'].delete()
        return {"message": "Unsubscribed successfully."}