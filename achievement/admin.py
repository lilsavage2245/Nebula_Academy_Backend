# achievement/admin.py

from django.contrib import admin
from achievement.models.badge import Badge, AwardedBadge
from achievement.models.award_log import BadgeAwardLog
from achievement.models.level import UserLevel
from achievement.models.profile import UserProfileAchievement
from achievement.models.xp import XPEvent


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'linked_to', 'achievement_type', 'rarity', 'xp_reward',
        'is_active', 'created_at', 'has_image'
    )
    list_filter = ('achievement_type', 'rarity', 'is_active', 'content_type')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at',)
    ordering = ('achievement_type', 'rarity', 'name')

    def has_image(self, obj):
        return bool(obj.image)
    has_image.boolean = True
    has_image.short_description = "Image Uploaded"

    def linked_to(self, obj):
        """Human-readable link target (e.g., 'Module: Web Dev')"""
        if obj.content_object:
            return f"{obj.content_type.model.capitalize()}: {str(obj.content_object)}"
        return "-"
    linked_to.short_description = "Linked To"



@admin.register(AwardedBadge)
class AwardedBadgeAdmin(admin.ModelAdmin):
    list_display = ('user', 'badge', 'awarded_at')
    list_filter = ('badge',)
    search_fields = ('user__email', 'badge__name')
    raw_id_fields = ('user', 'badge')
    readonly_fields = ('awarded_at',)
    ordering = ('-awarded_at',)


@admin.register(BadgeAwardLog)
class BadgeAwardLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'badge', 'source', 'awarded_at']
    #list_filter = ['source', 'badge__achievement_type']
    search_fields = ['user__email', 'badge__name']
    ordering = ['-awarded_at']


@admin.register(XPEvent)
class XPEventAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'xp', 'source', 'timestamp')
    list_filter = ('source',)
    search_fields = ('user__email', 'action')
    raw_id_fields = ('user', 'badge')
    readonly_fields = ('timestamp',)
    ordering = ('-timestamp',)


@admin.register(UserLevel)
class UserLevelAdmin(admin.ModelAdmin):
    list_display = ('level', 'title', 'xp_required')
    search_fields = ('title',)
    ordering = ('level',)


@admin.register(UserProfileAchievement)
class UserProfileAchievementAdmin(admin.ModelAdmin):
    list_display = ('user', 'total_xp', 'current_level', 'last_updated')
    search_fields = ('user__email',)
    raw_id_fields = ('user', 'current_level')
    readonly_fields = ('last_updated',)
    ordering = ('-total_xp',)
