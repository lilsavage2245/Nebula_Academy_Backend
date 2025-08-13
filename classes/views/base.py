# classes/views/base.py

from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied

class SoftDeleteMixin:
    """
    Overrides destroy to perform soft delete by setting is_active = False.
    """
    def perform_destroy(self, instance):
        if hasattr(instance, 'is_active'):
            instance.is_active = False
            instance.save()
        else:
            instance.delete()


class DynamicSerializerMixin:
    """
    Allows automatic switching between read and write serializers.
    Define `serializer_class` and `write_serializer_class`.
    """
    write_serializer_class = None

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update'] and self.write_serializer_class:
            return self.write_serializer_class
        return self.serializer_class


class FilteredLessonQuerysetMixin:
    """
    Adds query filtering support for lesson-level views.
    """
    def filter_queryset(self, queryset):
        qs = super().filter_queryset(queryset)
        module = self.request.query_params.get('module')
        level = self.request.query_params.get('program_level')
        session = self.request.query_params.get('session')
        if module:
            qs = qs.filter(module__slug=module)
        if level:
            qs = qs.filter(program_level__slug=level)
        if session:
            qs = qs.filter(session__id=session)
        return qs
