from rest_framework import serializers
from classes.models import (
    LessonQuiz, LessonQuizQuestion,
    LessonQuizResult, LessonQuizAnswer,
    Lesson,
)
from core.serializers import UserSerializer  # Assuming you use this
from django.utils.timesince import timesince


class LessonQuizQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonQuizQuestion
        fields = ['id', 'text', 'quiz', 'choices', 'correct_answer']
        extra_kwargs = {'correct_answer': {'write_only': True}}


class LessonQuizQuestionPublicSerializer(serializers.ModelSerializer):
    """Public-facing serializer that hides correct answer."""
    class Meta:
        model = LessonQuizQuestion
        fields = ['id', 'text', 'choices']


class LessonQuizSerializer(serializers.ModelSerializer):
    questions = LessonQuizQuestionPublicSerializer(many=True, read_only=True)
    lesson_id = serializers.PrimaryKeyRelatedField(source='lesson', read_only=True)

    class Meta:
        model = LessonQuiz
        fields = ['id', 'lesson_id', 'title', 'description', 'is_active', 'questions', 'created_at']
        read_only_fields = ['id', 'created_at']


class LessonQuizCreateUpdateSerializer(serializers.ModelSerializer):
    lesson = serializers.PrimaryKeyRelatedField(queryset=Lesson.objects.all())

    class Meta:
        model = LessonQuiz
        fields = ['lesson', 'title', 'description', 'is_active']

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)

class LessonQuizQuestionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonQuizQuestion
        fields = ['quiz', 'text', 'choices', 'correct_answer']


# --- For submitting a quiz attempt ---
class LessonQuizAnswerSubmitSerializer(serializers.Serializer):
    question_id = serializers.IntegerField()
    selected_answer = serializers.CharField()

    def validate(self, data):
        try:
            question = LessonQuizQuestion.objects.get(pk=data['question_id'])
        except LessonQuizQuestion.DoesNotExist:
            raise serializers.ValidationError("Invalid question ID.")
        if data['selected_answer'] not in question.choices:
            raise serializers.ValidationError("Selected answer is not in choices.")
        return data


class LessonQuizResultSubmitSerializer(serializers.Serializer):
    quiz_id = serializers.IntegerField()
    answers = LessonQuizAnswerSubmitSerializer(many=True)

    def validate_quiz_id(self, value):
        if not LessonQuiz.objects.filter(id=value, is_active=True).exists():
            raise serializers.ValidationError("Quiz not found or inactive.")
        return value

    def create(self, validated_data):
        quiz = LessonQuiz.objects.get(pk=validated_data['quiz_id'])
        user = self.context['request'].user
        answer_data = validated_data['answers']

        # Prevent retakes (optional)
        if LessonQuizResult.objects.filter(user=user, quiz=quiz).exists():
            raise serializers.ValidationError("You already attempted this quiz.")

        result = LessonQuizResult.objects.create(user=user, quiz=quiz)
        score = 0
        total = 0

        for answer in answer_data:
            question = LessonQuizQuestion.objects.get(id=answer['question_id'])
            is_correct = (answer['selected_answer'] == question.correct_answer)
            LessonQuizAnswer.objects.create(
                result=result,
                question=question,
                selected_answer=answer['selected_answer'],
                is_correct=is_correct
            )
            total += 1
            if is_correct:
                score += 1

        result.score = score
        result.passed = score >= int(0.6 * total)  # 60% pass mark (customize if needed)
        result.save()
        return result


class LessonQuizAnswerSerializer(serializers.ModelSerializer):
    question = LessonQuizQuestionPublicSerializer()

    class Meta:
        model = LessonQuizAnswer
        fields = ['question', 'selected_answer', 'is_correct']


class LessonQuizResultSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    quiz = LessonQuizSerializer(read_only=True)
    answers = LessonQuizAnswerSerializer(many=True, read_only=True)
    time_since = serializers.SerializerMethodField()

    class Meta:
        model = LessonQuizResult
        fields = ['id', 'user', 'quiz', 'score', 'passed', 'answers', 'submitted_at', 'time_since']

    def get_time_since(self, obj):
        return timesince(obj.submitted_at) + " ago"
