from django.contrib import admin
from django.utils.html import format_html
from news.models import (
    NewsCategory,
    NewsPost,
    NewsComment,
    NewsReaction,
    NewsSubscriber
)


# ---------- NewsCategory ----------
@admin.register(NewsCategory)
class NewsCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'description']
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ['name']
    ordering = ['name']


# ---------- Inlines ----------
class NewsCommentInline(admin.TabularInline):
    model = NewsComment
    fields = ['user', 'content', 'created_at', 'is_approved', 'is_deleted']
    readonly_fields = ['created_at']
    extra = 0
    show_change_link = True


class NewsReactionInline(admin.TabularInline):
    model = NewsReaction
    fields = ['user', 'reaction', 'reacted_at']
    readonly_fields = ['reacted_at']
    extra = 0
    show_change_link = False


# ---------- Actions ----------
@admin.action(description="✅ Approve selected comments")
def approve_selected_comments(modeladmin, request, queryset):
    updated = queryset.update(is_approved=True)
    modeladmin.message_user(request, f"{updated} comment(s) approved.")


# ---------- NewsPost ----------
@admin.register(NewsPost)
class NewsPostAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'author', 'status', 'published_on', 'created_at',
        'view_count', 'trending_status'
    ]
    list_filter = ['status', 'category', 'created_at', 'published_on']
    search_fields = ['title', 'summary', 'tags']
    prepopulated_fields = {"slug": ("title",)}
    inlines = [NewsCommentInline, NewsReactionInline]
    readonly_fields = ['view_count']
    ordering = ['-published_on', '-created_at']

    def trending_status(self, obj):
        if obj.view_count >= 1000:
            return format_html('<span style="color: red; font-weight: bold;">🔥 Trending</span>')
        return "-"
    trending_status.short_description = "Trending?"


# ---------- NewsComment ----------
@admin.register(NewsComment)
class NewsCommentAdmin(admin.ModelAdmin):
    list_display = ['content', 'user', 'post', 'created_at', 'is_approved', 'is_deleted', 'parent']
    list_filter = ['is_approved', 'is_deleted', 'created_at']
    search_fields = ['content', 'user__email', 'post__title']
    raw_id_fields = ['user', 'post', 'parent']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
    actions = [approve_selected_comments]
    list_editable = ['is_approved']


# ---------- NewsReaction ----------
@admin.register(NewsReaction)
class NewsReactionAdmin(admin.ModelAdmin):
    list_display = ['post', 'user', 'reaction', 'reacted_at', 'ip_address', 'device_id']
    list_filter = ['reaction', 'reacted_at']
    search_fields = ['post__title', 'user__email', 'ip_address', 'device_id']
    raw_id_fields = ['post', 'user']
    readonly_fields = ['reacted_at']
    ordering = ['-reacted_at']


# ---------- NewsSubscriber ----------
@admin.register(NewsSubscriber)
class NewsSubscriberAdmin(admin.ModelAdmin):
    list_display = ['user', 'get_target', 'source', 'subscribed_at']
    list_filter = ['source', 'subscribed_at']
    search_fields = ['user__email', 'category__name', 'author__email']
    raw_id_fields = ['user', 'category', 'author']
    readonly_fields = ['subscribed_at']
    ordering = ['-subscribed_at']

    def get_target(self, obj):
        if obj.category:
            return f"Category: {obj.category.name}"
        if obj.author:
            return f"Author: {obj.author.get_full_name()}"
        return '-'
    get_target.short_description = 'Subscribed To'
