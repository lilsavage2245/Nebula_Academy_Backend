# news/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedSimpleRouter

from news.views.category import NewsCategoryViewSet
from news.views.post import NewsPostViewSet
from news.views.comment import NewsCommentViewSet
from news.views.reaction import NewsReactionViewSet
from news.views.subscriber import NewsSubscriberViewSet

# Root-level routes
router = DefaultRouter()
router.register(r'categories', NewsCategoryViewSet, basename='news-category')
router.register(r'posts', NewsPostViewSet, basename='news-post')
router.register(r'comments', NewsCommentViewSet, basename='news-comment')  # global moderation
router.register(r'reactions', NewsReactionViewSet, basename='news-reaction')  # global stats
router.register(r'subscriptions', NewsSubscriberViewSet, basename='news-subscriber')

# Nested under /posts/{post_slug}/
post_router = NestedSimpleRouter(router, r'posts', lookup='post')
post_router.register(r'comments', NewsCommentViewSet, basename='post-comments')
post_router.register(r'reactions', NewsReactionViewSet, basename='post-reactions')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(post_router.urls)),
]
