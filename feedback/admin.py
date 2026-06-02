from django.contrib import admin
from django.utils.html import format_html
from .models import (FacultyProfile, StudentProfile, Course,
                     Survey, CourseOutcome, Question, MCQOption,
                     SurveyResponse, Answer)


class CourseOutcomeInline(admin.TabularInline):
    model    = CourseOutcome
    extra    = 3
    fields   = ['code', 'description']
    ordering = ['code']


class MCQOptionInline(admin.TabularInline):
    model    = MCQOption
    extra    = 3
    fields   = ['option_text', 'order']
    ordering = ['order']


class QuestionInline(admin.TabularInline):
    model            = Question
    extra            = 1
    fields           = ['text', 'question_type', 'order', 'is_required', 'mapped_to_co']
    ordering         = ['order']
    show_change_link = True


class SurveyInline(admin.TabularInline):
    model            = Survey
    extra            = 0
    fields           = ['title', 'is_published', 'start_date', 'end_date']
    show_change_link = True


@admin.register(FacultyProfile)
class FacultyProfileAdmin(admin.ModelAdmin):
    list_display  = ['full_name', 'employee_id', 'department', 'designation']
    list_filter   = ['department']
    search_fields = ['user__first_name', 'user__last_name', 'employee_id', 'department']

    @admin.display(description='Name')
    def full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display  = ['full_name', 'enrollment_no', 'branch', 'semester', 'batch']
    list_filter   = ['branch', 'semester', 'batch']
    search_fields = ['user__first_name', 'user__last_name', 'enrollment_no', 'branch']

    @admin.display(description='Name')
    def full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display      = ['code', 'name', 'faculty_name', 'semester', 'batch', 'credits']
    list_filter       = ['semester', 'batch']
    search_fields     = ['code', 'name']
    filter_horizontal = ['students']
    inlines           = [CourseOutcomeInline, SurveyInline]

    @admin.display(description='Faculty')
    def faculty_name(self, obj):
        return obj.faculty.user.get_full_name() if obj.faculty else '—'


@admin.register(Survey)
class SurveyAdmin(admin.ModelAdmin):
    list_display    = ['title', 'course_code', 'is_published',
                       'active_badge', 'start_date', 'end_date', 'response_count']
    list_filter     = ['is_published', 'course__semester']
    search_fields   = ['title', 'course__name', 'course__code']
    inlines         = [QuestionInline]
    actions         = ['publish_selected', 'unpublish_selected']
    readonly_fields = ['created_at', 'updated_at']

    @admin.display(description='Course')
    def course_code(self, obj):
        return obj.course.code

    @admin.display(description='Active Now', boolean=True)
    def active_badge(self, obj):
        return obj.is_active()

    @admin.display(description='Responses')
    def response_count(self, obj):
        count = obj.responses.count()
        color = '#16a34a' if count > 0 else '#9ca3af'
        return format_html('<span style="font-weight:600;color:{}">{}</span>', color, count)

    @admin.action(description='Publish selected surveys')
    def publish_selected(self, request, queryset):
        updated = queryset.update(is_published=True)
        self.message_user(request, f'{updated} survey(s) published.')

    @admin.action(description='Unpublish selected surveys')
    def unpublish_selected(self, request, queryset):
        updated = queryset.update(is_published=False)
        self.message_user(request, f'{updated} survey(s) unpublished.')


@admin.register(CourseOutcome)
class CourseOutcomeAdmin(admin.ModelAdmin):
    list_display  = ['course', 'code', 'description_short']
    list_filter   = ['course']
    search_fields = ['code', 'description', 'course__code']

    @admin.display(description='Description')
    def description_short(self, obj):
        return obj.description[:80]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display  = ['short_text', 'survey', 'question_type', 'mapped_to_co', 'order', 'is_required']
    list_filter   = ['question_type', 'is_required']
    search_fields = ['text']
    inlines       = [MCQOptionInline]

    @admin.display(description='Question')
    def short_text(self, obj):
        return obj.text[:70]


@admin.register(MCQOption)
class MCQOptionAdmin(admin.ModelAdmin):
    list_display  = ['option_text', 'question', 'order']
    search_fields = ['option_text']


@admin.register(SurveyResponse)
class SurveyResponseAdmin(admin.ModelAdmin):
    list_display    = ['student_name', 'survey', 'submitted_at', 'is_anonymous']
    list_filter     = ['is_anonymous', 'survey', 'submitted_at']
    search_fields   = ['student__enrollment_no', 'student__user__first_name']
    readonly_fields = ['survey', 'student', 'submitted_at']

    @admin.display(description='Student')
    def student_name(self, obj):
        return obj.student.user.get_full_name()


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display    = ['response', 'question_short', 'question_type_display',
                       'rating_value', 'yes_no_value', 'mcq_choice']
    list_filter     = ['question__question_type']
    search_fields   = ['response__student__enrollment_no']
    readonly_fields = ['response', 'question']

    @admin.display(description='Question')
    def question_short(self, obj):
        return obj.question.text[:60]

    @admin.display(description='Type')
    def question_type_display(self, obj):
        return obj.question.get_question_type_display()