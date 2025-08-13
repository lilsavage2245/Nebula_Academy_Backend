# news/serializers/reaction.py

from rest_framework import serializers
from django.utils.timesince import timesince
from news.models import NewsReaction
from core.serializers import UserSerializer


class NewsReactionSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    reaction_display = serializers.CharField(source='get_reaction_display', read_only=True)
    reacted_at_display = serializers.SerializerMethodField()

    class Meta:
        model = NewsReaction
        fields = [
            'id', 'post', 'user', 'reaction', 'reaction_display',
            'reacted_at', 'reacted_at_display',
            'ip_address', 'device_id'
        ]
        read_only_fields = ['id', 'user', 'reacted_at', 'reaction_display', 'reacted_at_display']

    def get_reacted_at_display(self, obj):
        return timesince(obj.reacted_at) + " ago" if obj.reacted_at else None

class NewsReactionCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsReaction
        fields = ['post', 'reaction', 'ip_address', 'device_id']

    def validate(self, attrs):
        if not self.context.get('request'):
            raise serializers.ValidationError("Missing request context for user resolution.")
        return attrs

    def create(self, validated_data):
        user = self.context['request'].user
        post = validated_data['post']
        reaction = validated_data['reaction']

        instance, created = NewsReaction.objects.update_or_create(
            user=user,
            post=post,
            defaults={
                'reaction': reaction,
                'ip_address': validated_data.get('ip_address'),
                'device_id': validated_data.get('device_id')
            }
        )

        # Attach instance to serializer so view can access .instance
        self.instance = instance

        if not created:
            self.context['updated'] = True  # Let view catch this if needed

        return instance
