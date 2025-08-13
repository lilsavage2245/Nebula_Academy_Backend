# classes/admin.py

from django.contrib import admin
from classes.models import (
    Lesson, LessonMaterial,
    LessonComment, LessonReply, LessonRating,
    LessonAttendance, LessonQuiz, LessonQuizAnswer,
    LessonQuizResult, LessonQuizQuestion
)


# --- Inlines for rich nested admin in Lesson ---
class LessonMaterialInline(admin.TabularInline):
    model = LessonMaterial
    extra = 0
    fields = ('title', 'material_type', 'version', 'audience', 'uploaded_by', 'created_at')
    readonly_fields = ('created_at',)
    show_change_link = True
    autocomplete_fields = ('uploaded_by',)


class LessonCommentInline(admin.TabularInline):
    model = LessonComment
    extra = 0
    fields = ('user', 'content', 'created_at')
    readonly_fields = ('created_at',)
    show_change_link = True
    autocomplete_fields = ('user',)


class LessonReplyInline(admin.TabularInline):
    model = LessonReply
    extra = 0
    fields = ('user', 'parent_comment', 'content', 'created_at')
    readonly_fields = ('created_at',)
    autocomplete_fields = ('user', 'parent_comment')


class LessonRatingInline(admin.TabularInline):
    model = LessonRating
    extra = 0
    fields = ('user', 'score', 'review', 'created_at')
    readonly_fields = ('created_at',)
    autocomplete_fields = ('user',)


class LessonAttendanceInline(admin.TabularInline):
    model = LessonAttendance
    extra = 0
    fields = ('user', 'attended', 'timestamp')
    readonly_fields = ('timestamp',)
    autocomplete_fields = ('user',)

class LessonQuizInline(admin.TabularInline):
    model = LessonQuiz
    extra = 0
    fields = ('title', 'description', 'is_active', 'created_at')
    readonly_fields = ('created_at',)
    show_change_link = True

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'program_level', 'module', 'session',
        'date', 'delivery', 'audience', 'is_published', 'is_active'
    )
    list_filter = ('program_level', 'module', 'session', 'delivery', 'audience', 'is_published', 'is_active')
    search_fields = ('title', 'description', 'slug')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('created_at',)
    date_hierarchy = 'date'
    ordering = ['-date']
    inlines = [
        LessonMaterialInline,
        LessonCommentInline,
        LessonRatingInline,
        LessonAttendanceInline,
        LessonQuizInline,
    ]
    autocomplete_fields = ('program_level', 'module', 'session')

# --- Quiz Models ---
class LessonQuizQuestionInline(admin.TabularInline):
    model = LessonQuizQuestion
    extra = 0
    fields = ('text', 'choices', 'correct_answer')
    show_change_link = True


@admin.register(LessonQuiz)
class LessonQuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'lesson', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('title', 'lesson__title')
    readonly_fields = ('created_at',)
    inlines = [LessonQuizQuestionInline]
    autocomplete_fields = ('lesson',)
    ordering = ('-created_at',)


@admin.register(LessonQuizResult)
class LessonQuizResultAdmin(admin.ModelAdmin):
    list_display = ('user', 'quiz', 'score', 'passed', 'submitted_at')
    list_filter = ('passed',)
    search_fields = ('user__email', 'quiz__title')
    readonly_fields = ('submitted_at',)
    autocomplete_fields = ('user', 'quiz')


@admin.register(LessonQuizAnswer)
class LessonQuizAnswerAdmin(admin.ModelAdmin):
    list_display = ('result', 'question', 'selected_answer', 'is_correct')
    search_fields = ('result__user__email', 'question__text', 'selected_answer')
    autocomplete_fields = ('result', 'question')

@admin.register(LessonQuizQuestion)
class LessonQuizQuestionAdmin(admin.ModelAdmin):
    list_display = ('quiz', 'text')
    search_fields = ('text', 'quiz__title')
    autocomplete_fields = ('quiz',)

    
@admin.register(LessonMaterial)
class LessonMaterialAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'lesson', 'material_type', 'audience',
        'version', 'is_active', 'created_at'
    )
    list_filter = ('material_type', 'audience', 'is_active')
    search_fields = ('title', 'lesson__title')
    readonly_fields = ('created_at',)
    autocomplete_fields = ('lesson', 'uploaded_by')
    ordering = ('-created_at',)


@admin.register(LessonComment)
class LessonCommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'lesson', 'created_at')
    search_fields = ('content', 'user__email', 'lesson__title')
    readonly_fields = ('created_at',)
    autocomplete_fields = ('user', 'lesson')
    ordering = ('-created_at',)


@admin.register(LessonReply)
class LessonReplyAdmin(admin.ModelAdmin):
    list_display = ('user', 'parent_comment', 'created_at')
    search_fields = ('content', 'user__email', 'parent_comment__lesson__title')
    readonly_fields = ('created_at',)
    autocomplete_fields = ('user', 'parent_comment')
    ordering = ('created_at',)


@admin.register(LessonRating)
class LessonRatingAdmin(admin.ModelAdmin):
    list_display = ('user', 'lesson', 'score', 'created_at')
    list_filter = ('score',)
    search_fields = ('user__email', 'lesson__title', 'review')
    readonly_fields = ('created_at',)
    autocomplete_fields = ('user', 'lesson')
    ordering = ('-created_at',)


@admin.register(LessonAttendance)
class LessonAttendanceAdmin(admin.ModelAdmin):
    list_display = ('user', 'lesson', 'attended', 'timestamp')
    list_filter = ('attended',)
    search_fields = ('user__email', 'lesson__title')
    readonly_fields = ('timestamp',)
    autocomplete_fields = ('user', 'lesson')
    ordering = ('-timestamp',)
