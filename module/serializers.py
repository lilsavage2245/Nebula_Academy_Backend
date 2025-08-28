from rest_framework import serializers
from django.core.exceptions import ValidationError
from django.utils.text import slugify

from .models import (
    Module, ModuleLevelLink, ModuleLecturer,
    EvaluationComponent, ModuleMaterial,
    MaterialAudience, MaterialType
)
from program.models import ProgramLevel
from core.serializers import UserSerializer  # for lecturers


# ---------- Evaluation Component ----------
class EvaluationComponentSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source='get_type_display', read_only=True)

    class Meta:
        model = EvaluationComponent
        fields = [
            'id', 'type', 'type_display', 'title', 'criteria',
            'weight', 'created_at', 'updated_at'
        ]


# ---------- Module Lecturer ----------
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


# ---------- Module Level Link ----------
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


# ---------- Module Material (READ) ----------
class ModuleMaterialSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    audience_display = serializers.CharField(source='get_audience_display', read_only=True)

    file_url = serializers.SerializerMethodField()
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = ModuleMaterial
        fields = [
            'id', 'title', 'slug', 'description',
            'type', 'type_display',
            'audience', 'audience_display',
            'file_url', 'download_url', 'external_url',
            'content_type', 'file_size',
            'version', 'is_active', 'created_at',
        ]
        read_only_fields = ['slug', 'created_at', 'file_url', 'download_url']

    def get_file_url(self, obj: ModuleMaterial):
        """
        Direct storage URL for preview (public or signed by storage).
        Use only if you allow preview; otherwise rely on download_url.
        """
        request = self.context.get('request')
        if obj.file and hasattr(obj.file, 'url') and request:
            try:
                return request.build_absolute_uri(obj.file.url)
            except Exception:
                return None
        return None

    def get_download_url(self, obj: ModuleMaterial):
        """
        Protected, permission-checked endpoint you’ll implement in the ViewSet:
        /api/modules/<module_slug>/materials/<material_slug>/download/
        """
        request = self.context.get('request')
        if not request:
            return None
        return request.build_absolute_uri(
            f"/api/modules/{obj.module.slug}/materials/{obj.slug}/download/"
        )


# ---------- Module Material (CREATE/UPDATE) ----------
class ModuleMaterialCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModuleMaterial
        # slug is auto-generated in model.save()
        fields = [
            'title', 'description',
            'type', 'audience',
            'file', 'external_url',
            'version', 'is_active',
        ]

    def validate(self, attrs):
        material_type = attrs.get('type', getattr(self.instance, 'type', None))
        file = attrs.get('file', getattr(self.instance, 'file', None))
        external_url = attrs.get('external_url', getattr(self.instance, 'external_url', None))

        has_file = bool(file)
        has_link = bool(external_url)

        # Type-specific source validation
        if material_type == MaterialType.LINK:
            if not has_link:
                raise ValidationError("LINK material must include an external_url.")
            if has_file:
                raise ValidationError("LINK material should not include a file.")
        else:
            # PDF / SLIDES / OTHER must have at least one source
            if not has_file and not has_link:
                raise ValidationError("Provide a file or an external_url for this material.")
        return attrs


# ---------- Module (READ) ----------
class ModuleSerializer(serializers.ModelSerializer):
    slug = serializers.SlugField(read_only=True)

    # Nested read
    levels = ModuleLevelLinkSerializer(source='modulelevellink_set', many=True, read_only=True)
    lecturers = ModuleLecturerSerializer(source='modulelecturer_set', many=True, read_only=True)
    materials = ModuleMaterialSerializer(many=True, read_only=True)
    evaluations = EvaluationComponentSerializer(many=True, read_only=True)


    class Meta:
        model = Module
        fields = [
            'id', 'title', 'slug', 'description', 'prerequisites', 'tools_software',
            'is_standalone', 'is_active', 'created_at', 'updated_at',
            'levels', 'lecturers', 'materials', 'evaluations',
        ]
        read_only_fields = ['slug', 'created_at', 'updated_at']



# ---------- Module (CREATE/UPDATE) ----------
class ModuleCreateUpdateSerializer(serializers.ModelSerializer):
    # Nested writes (optional)
    levels = ModuleLevelLinkSerializer(many=True, write_only=True, required=False)
    lecturers = ModuleLecturerSerializer(many=True, write_only=True, required=False)
    materials = ModuleMaterialCreateUpdateSerializer(many=True, write_only=True, required=False)

    class Meta:
        model = Module
        fields = [
            'title', 'description', 'prerequisites', 'tools_software',
            'is_standalone', 'is_active',
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
            ModuleMaterial.objects.create(module=module, **item)

        return module

    def update(self, instance, validated_data):
        levels_data = validated_data.pop('levels', None)
        lecturers_data = validated_data.pop('lecturers', None)
        materials_data = validated_data.pop('materials', None)  # optional bulk replace

        # Basic fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Replace levels if provided
        if levels_data is not None:
            instance.modulelevellink_set.all().delete()
            for item in levels_data:
                ModuleLevelLink.objects.create(module=instance, **item)

        # Replace lecturers if provided
        if lecturers_data is not None:
            instance.modulelecturer_set.all().delete()
            for item in lecturers_data:
                ModuleLecturer.objects.create(module=instance, **item)

        # Strategy for materials:
        # By default this performs a "replace all" if provided (simple & predictable).
        if materials_data is not None:
            instance.materials.all().delete()
            for item in materials_data:
                ModuleMaterial.objects.create(module=instance, **item)

        return instance
