# module/serializers.py
from rest_framework import serializers
from .models import (
    Module, ModuleLevelLink, ModuleLecturer,
    LectureMaterial, EvaluationComponent
)
from achievement.models import Badge
from program.models import ProgramLevel
from core.serializers import UserSerializer  # assuming you have this for lecturers


# --- Badge Serializer ---
class BadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badge
        fields = ['id', 'name', 'criteria', 'image', 'created_at']


# --- Evaluation Component Serializer ---
class EvaluationComponentSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source='get_type_display', read_only=True)

    class Meta:
        model = EvaluationComponent
        fields = [
            'id', 'type', 'type_display', 'title', 'criteria',
            'weight', 'created_at', 'updated_at'
        ]


# --- Lecture Material Serializer ---
class LectureMaterialSerializer(serializers.ModelSerializer):
    audience_display = serializers.CharField(source='get_audience_display', read_only=True)
    file_size = serializers.SerializerMethodField()
    file_type = serializers.SerializerMethodField()

    class Meta:
        model = LectureMaterial
        fields = [
            'id', 'title', 'audience', 'audience_display',
            'slides', 'video_url', 'created_at',
            'file_size', 'file_type'
        ]

    def get_file_size(self, obj):
        if obj.slides:
            return obj.slides.size  # in bytes
        return 0

    def get_file_type(self, obj):
        if obj.slides and hasattr(obj.slides, 'name'):
            return obj.slides.name.split('.')[-1].lower()
        return None



# --- ModuleLecturer Serializer (Read + Write) ---
class ModuleLecturerSerializer(serializers.ModelSerializer):
    lecturer = UserSerializer(read_only=True)
    lecturer_id = serializers.PrimaryKeyRelatedField(
        queryset=UserSerializer.Meta.model.objects.filter(role='LECTURER'),
        source='lecturer',
        write_only=True
    )

    class Meta:
        model = ModuleLecturer
        fields = ['id', 'lecturer', 'lecturer_id', 'role']


# --- ModuleLevelLink Serializer (for nested listing) ---
class ModuleLevelLinkSerializer(serializers.ModelSerializer):
    level_id = serializers.PrimaryKeyRelatedField(
        source='level',
        queryset=ProgramLevel.objects.all(),
        write_only=True
    )
    level_display = serializers.CharField(source='level.title', read_only=True)

    class Meta:
        model = ModuleLevelLink
        fields = ['id', 'level_id', 'level_display', 'order']



# --- Main Module Serializer ---
class ModuleSerializer(serializers.ModelSerializer):
    slug = serializers.SlugField(read_only=True)
    levels = ModuleLevelLinkSerializer(source='modulelevellink_set', many=True, read_only=True)
    lecturers = ModuleLecturerSerializer(source='modulelecturer_set', many=True, read_only=True)
    materials = LectureMaterialSerializer(many=True, read_only=True)
    evaluations = EvaluationComponentSerializer(many=True, read_only=True)
    badge = BadgeSerializer(read_only=True)

    class Meta:
        model = Module
        fields = [
            'id', 'title', 'slug', 'description',
            'is_standalone', 'created_at', 'updated_at',
            'levels', 'lecturers', 'materials', 'evaluations', 'badge'
        ]
        read_only_fields = ['slug', 'created_at', 'updated_at']


class ModuleCreateUpdateSerializer(serializers.ModelSerializer):
    levels = ModuleLevelLinkSerializer(many=True, write_only=True, required=False)
    lecturers = ModuleLecturerSerializer(many=True, write_only=True, required=False)
    materials = LectureMaterialSerializer(many=True, write_only=True, required=False)

    class Meta:
        model = Module
        fields = [
            'title', 'description', 'is_standalone',
            'levels', 'lecturers', 'materials'
        ]

    def create(self, validated_data):
        levels_data = validated_data.pop('levels', [])
        lecturers_data = validated_data.pop('lecturers', [])
        materials_data = validated_data.pop('materials', [])

        module = Module.objects.create(**validated_data)

        # Levels
        for item in levels_data:
            ModuleLevelLink.objects.create(module=module, **item)

        # Lecturers
        for item in lecturers_data:
            ModuleLecturer.objects.create(module=module, **item)

        # Materials
        for item in materials_data:
            LectureMaterial.objects.create(module=module, **item)

        return module

    def update(self, instance, validated_data):
        levels_data = validated_data.pop('levels', None)
        lecturers_data = validated_data.pop('lecturers', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if levels_data is not None:
            instance.modulelevellink_set.all().delete()
            for item in levels_data:
                ModuleLevelLink.objects.create(module=instance, **item)

        if lecturers_data is not None:
            instance.modulelecturer_set.all().delete()
            for item in lecturers_data:
                ModuleLecturer.objects.create(module=instance, **item)

        return instance
