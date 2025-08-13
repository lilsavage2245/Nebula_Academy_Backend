# news/seriaalizers/comment.py

from rest_framework import serializers
from django.utils.timesince import timesince
from news.models import NewsComment
from core.serializers import UserSerializer

class ReplySerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    time_since_posted = serializers.SerializerMethodField()

    class Meta:
        model = NewsComment
        fields = [
            'id', 'content', 'user',
            'created_at', 'updated_at',
            'time_since_posted'
        ]

    def get_time_since_posted(self, obj):
        return timesince(obj.created_at) + " ago" if obj.created_at else None

class NewsCommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    replies = ReplySerializer(many=True, read_only=True)
    time_since_posted = serializers.SerializerMethodField()
    depth = serializers.SerializerMethodField()
    is_reply = serializers.SerializerMethodField()

    class Meta:
        model = NewsComment
        fields = [
            'id', 'post', 'content', 'user',
            'created_at', 'updated_at', 'time_since_posted',
            'parent', 'is_reply', 'depth',
            'replies',
            'is_approved', 'is_deleted'
        ]
        read_only_fields = [
            'user', 'created_at', 'updated_at',
            'time_since_posted', 'replies', 'is_reply', 'depth',
            'is_approved', 'is_deleted'
        ]

    def get_time_since_posted(self, obj):
        return timesince(obj.created_at) + " ago" if obj.created_at else None

    def get_depth(self, obj):
        return obj.nesting_depth

    def get_is_reply(self, obj):
        return obj.is_reply()

class NewsCommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsComment
        fields = ['post', 'content']

class ReplyCreateSerializer(serializers.ModelSerializer):
    parent_id = serializers.PrimaryKeyRelatedField(
        source='parent',
        queryset=NewsComment.objects.all(),
        write_only=True
    )

    class Meta:
        model = NewsComment
        fields = ['post', 'parent_id', 'content']

    def validate(self, attrs):
        parent = attrs.get("parent")
        if parent and parent.nesting_depth >= 1:
            raise serializers.ValidationError("Only one level of nested replies is allowed.")
        return super().validate(attrs)
