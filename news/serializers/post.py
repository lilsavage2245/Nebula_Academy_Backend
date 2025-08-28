# news/serializers/post.py
from rest_framework import serializers
from django.utils.timesince import timesince
from news.models import NewsPost
from core.serializers import UserSerializer
from news.serializers.category import NewsCategorySerializer

class NewsPostSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    category = NewsCategorySerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_visible = serializers.BooleanField(read_only=True)
    time_since_published = serializers.SerializerMethodField()

    class Meta:
        model = NewsPost
        fields = [
            'id', 'title', 'slug',
            'author', 'category',
            'summary', 'content', 'content_html', 'image', 'tags',
            'status', 'status_display', 'is_visible',
            'allow_comments', 'view_count',
            'meta_title', 'meta_description',
            'published_on', 'time_since_published',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'slug', 'status_display', 'view_count',
            'created_at', 'updated_at', 'is_visible', 'time_since_published'
        ]

    def get_time_since_published(self, obj):
        if obj.published_on:
            return timesince(obj.published_on) + " ago"
        return None

from rest_framework import serializers
from django.utils import timezone
from news.models import NewsPost

class NewsPostCreateUpdateSerializer(serializers.ModelSerializer):
    author_id = serializers.PrimaryKeyRelatedField(
        queryset=NewsPost._meta.get_field('author').remote_field.model.objects.all(),
        source='author',
        write_only=True
    )
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=NewsPost._meta.get_field('category').remote_field.model.objects.all(),
        source='category',
        write_only=True,
        required=False
    )

    class Meta:
        model = NewsPost
        fields = [
            'title', 'summary', 'content', 'image', 'tags',
            'status', 'allow_comments',
            'meta_title', 'meta_description',
            'author_id', 'category_id',
        ]

    def validate(self, attrs):
        # Auto-set published_on if status is 'PUBLISHED' and no value exists
        if (
            attrs.get('status') == NewsPost.Status.PUBLISHED
            and (not self.instance or not self.instance.published_on)
        ):
            attrs['published_on'] = timezone.now()
        return super().validate(attrs)
