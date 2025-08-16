# program/serializers.py
from rest_framework import serializers
from .models import Program, ProgramLevel, Session, ProgramCategory
from django.contrib.auth import get_user_model

User = get_user_model()

# -- Director Info (for nested read access) --
class DirectorSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'email']

# -- Program Level Serializer --
class ProgramLevelSerializer(serializers.ModelSerializer):
    program_name = serializers.CharField(source='program.name', read_only=True)
    class Meta:
        model = ProgramLevel
        fields = ['id', 'level_number', 'title', 'description', 'program_name']

# -- Session Serializer with level linking --
class SessionSerializer(serializers.ModelSerializer):
    level = serializers.StringRelatedField(read_only=True)
    level_id = serializers.PrimaryKeyRelatedField(
        source='level',
        queryset=ProgramLevel.objects.all(),
        write_only=True
    )
    program_name = serializers.CharField(source='level.program.name', read_only=True)

    class Meta:
        model = Session
        fields = [
            'id',
            'title',
            'mode',
            'start_datetime',
            'end_datetime',
            'location',
            'level',
            'level_id',
            'program_name',
        ]
        read_only_fields = ['id']



# -- Main Program Serializer --
class ProgramSerializer(serializers.ModelSerializer):
    director = DirectorSerializer(read_only=True)
    director_id = serializers.PrimaryKeyRelatedField(
        source='director',
        queryset=User.objects.filter(is_active=True, role='ADMIN'),
        write_only=True
    )
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    levels = ProgramLevelSerializer(many=True, read_only=True)

    class Meta:
        model = Program
        fields = [
            'id',
            'name',
            'slug',
            'category',
            'category_display',
            'description',
            'director',
            'director_id',
            'created_at',
            'updated_at',
            'levels',
        ]
        read_only_fields = ['slug', 'created_at', 'updated_at']

# -- Optional: For listing category choices in the API (e.g., dropdown) --
class ProgramCategorySerializer(serializers.Serializer):
    value = serializers.CharField()
    label = serializers.CharField()

    @classmethod
    def from_enum(cls):
        return [
            {"value": k, "label": v}
            for k, v in ProgramCategory.choices
        ]
