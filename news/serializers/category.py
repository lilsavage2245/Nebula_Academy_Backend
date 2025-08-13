# news/serializers/category.py
from rest_framework import serializers
from news.models import NewsCategory


class NewsCategorySerializer(serializers.ModelSerializer):
    post_count = serializers.SerializerMethodField()

    class Meta:
        model = NewsCategory
        fields = [
            'id',
            'name',
            'slug',
            'description',
            'icon',
            'post_count',
        ]
        read_only_fields = ['slug', 'post_count']

    def get_post_count(self, obj):
        return obj.posts.count()
