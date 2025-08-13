from django.utils import timezone
from news.models import NewsPost, NewsCategory
from django.contrib.auth import get_user_model

User = get_user_model()

# Setup test data
def create_test_user():
    return User.objects.create_user(
        email="testuser@example.com",
        password="testpass123",
        first_name="Test",
        last_name="User",
        role="BLOGGER"
    )

# Test functions for SlugModelMixin behavior
def test_news_category_slug_generation(db):
    category1 = NewsCategory.objects.create(name="Tech News")
    category2 = NewsCategory.objects.create(name="Tech News!")

    assert category1.slug == "tech-news"
    assert category2.slug.startswith("tech-news-")
    assert category1.slug != category2.slug

def test_news_post_slug_generation(db):
    author = create_test_user()

    post1 = NewsPost.objects.create(
        title="AI Takes Over",
        author=author,
        content="Content A",
        status="DRAFT"
    )
    post2 = NewsPost.objects.create(
        title="AI Takes Over",
        author=author,
        content="Content B",
        status="DRAFT"
    )

    assert post1.slug == "ai-takes-over"
    assert post2.slug.startswith("ai-takes-over-")
    assert post1.slug != post2.slug

def test_news_post_slug_published_timestamp(db):
    author = create_test_user()

    post = NewsPost.objects.create(
        title="Launch Day",
        author=author,
        content="Important announcement.",
        status="PUBLISHED"
    )

    assert post.slug == "launch-day"
    assert post.published_on is not None
