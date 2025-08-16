# application/serializers.py
from rest_framework import serializers
from .models import Application, ApplicationType, ApplicationStatus

class ApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = [
            "id", "applicant", "type", "program", "level", "module",
            "status", "applicant_note", "supporting_documents",
            "reviewer", "review_comment",
            "answers", "form_key",
            "submitted_on", "reviewed_on",
            "created_at", "updated_at",
        ]
        read_only_fields = (
            "applicant", "status", "submitted_on", "reviewed_on",
            "created_at", "updated_at",
        )

    def validate(self, data):
        """
        Rules:
        - PROGRAM apps:
            * require program OR level (if level only, infer program = level.program)
            * forbid module
            * if both program+level present, ensure level.program == program
        - MODULE apps:
            * require module
            * forbid program and level
        """
        instance = getattr(self, "instance", None)

        # resolve current values with PATCH-friendly precedence
        t = data.get("type") or (instance.type if instance else None)
        program = data.get("program") if "program" in data else (instance.program if instance else None)
        level   = data.get("level")   if "level"   in data else (instance.level   if instance else None)
        module  = data.get("module")  if "module"  in data else (instance.module  if instance else None)

        if not t:
            raise serializers.ValidationError({"type": "Application type is required."})

        errors = {}

        if t == ApplicationType.PROGRAM:
            # Forbid module
            if module:
                errors["module"] = "Must be empty for PROGRAM applications."

            # Allow level-only by inferring program
            if not program and level:
                program = level.program
                data["program"] = program  # persist inference

            # Require at least program or level
            if not program and not level:
                errors["program"] = "Program or Level is required for PROGRAM applications."
                errors["level"] = "Provide a level if program is not supplied."

            # If both provided, ensure they match
            if program and level and level.program_id != program.id:
                errors["level"] = "Level does not belong to the selected Program."

        elif t == ApplicationType.MODULE:
            # Require module
            if not module:
                errors["module"] = "Module is required for MODULE applications."
            # Forbid program and level
            if program:
                errors["program"] = "Must be empty for MODULE applications."
            if level:
                errors["level"] = "Must be empty for MODULE applications."
        else:
            errors["type"] = "Unknown application type."

        if errors:
            raise serializers.ValidationError(errors)

        return data

    def create(self, validated_data):
        # Attach the authenticated user as applicant
        request = self.context.get("request")
        if request and request.user and request.user.is_authenticated:
            validated_data["applicant"] = request.user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Prevent client from changing immutable fields post-create (optional hardening)
        validated_data.pop("applicant", None)
        # If you want type to be immutable after creation, uncomment:
        # validated_data.pop("type", None)
        return super().update(instance, validated_data)
