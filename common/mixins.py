# common/mixins.py
from django.db import models
from common.utils import generate_unique_slug


# ========== Slug Mixin ==========
class SlugModelMixin(models.Model):
    """
    Abstract model to automatically generate a unique slug
    based on a specified source field.
    """
    slug_field_name = 'slug'
    slug_source_field = 'title'
    slug_max_length = 150

    class Meta:
        abstract = True

    def generate_slug(self):
        base_value = getattr(self, self.slug_source_field)
        slug = generate_unique_slug(
            self,
            base_value,
            slug_field_name=self.slug_field_name,
            max_length=self.slug_max_length
        )
        setattr(self, self.slug_field_name, slug)

    def save(self, *args, **kwargs):
        if not getattr(self, self.slug_field_name):
            self.generate_slug()
        super().save(*args, **kwargs)


# ========== Scoped Query Mixin ==========
class ModuleScopedQueryMixin:
    """
    For viewsets that should filter content by module slug from URL.
    """
    def get_queryset(self):
        qs = super().get_queryset()
        module_slug = self.kwargs.get('module_slug')
        if module_slug:
            return qs.filter(module__slug=module_slug)
        return qs.none()  # fail-safe


# ========== Lesson Visibility Filter ==========
def filter_lessons_by_audience(qs, user):
    """
    Filter lessons queryset based on user access:
    - Staff see everything
    - Enrolled users see all except STAFF-only lessons
    - Free/unauthenticated users see only FREE and BOTH
    """
    if user.is_staff:
        return qs

    if user.is_authenticated:
        if getattr(user, 'is_enrolled', False):
            return qs.exclude(audience='STAFF')
        return qs.filter(audience__in=['FREE', 'BOTH'])

    return qs.filter(audience__in=['FREE', 'BOTH'])

# ========== Soft Delete Mixin ==========
class SoftDeleteModelMixin(models.Model):
    """
    Reusable mixin for soft deletion support.
    """
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        self.is_active = False
        self.save()
