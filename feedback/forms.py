"""
feedback/forms.py
=================
ModelForms for Survey creation and the HTMX-driven builder page.

Key adaptations to match our actual models:
  - Survey uses start_date / end_date (not open_date / close_date)
  - CourseOutcome has no 'order' field — linked to Course, not Survey
  - Question uses mapped_to_co (ForeignKey to CourseOutcome)
"""

from django import forms
from .models import Survey, CourseOutcome, Question, Course


# ── Shared Tailwind widget class ──────────────────────────────────────────────
FIELD_CLASS = (
    'form-input'
)


# ── Survey Form ───────────────────────────────────────────────────────────────

class SurveyForm(forms.ModelForm):
    """
    Used on the survey_create page.
    Faculty sees only their own courses in the dropdown.
    """
    class Meta:
        model  = Survey
        fields = ['course', 'title', 'description', 'start_date', 'end_date']
        widgets = {
            'start_date' : forms.DateTimeInput(
                attrs={'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M'
            ),
            'end_date': forms.DateTimeInput(
                attrs={'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M'
            ),
            'description': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, faculty, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show courses that belong to THIS faculty
        self.fields['course'].queryset = Course.objects.filter(faculty=faculty)
        self.fields['description'].required = False
        # Apply styling to every field
        for field in self.fields.values():
            existing = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = FIELD_CLASS + ' ' + existing


# ── Course Outcome Form ───────────────────────────────────────────────────────

class CourseOutcomeForm(forms.ModelForm):
    """
    Used in the HTMX panel of survey_detail.
    Adds a CO to the survey's course (COs belong to Course, not Survey).
    """
    class Meta:
        model  = CourseOutcome
        fields = ['code', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['code'].widget.attrs.update({
            'placeholder': 'e.g. CO1'
        })
        for field in self.fields.values():
            existing = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = FIELD_CLASS + ' ' + existing


# ── Question Form ─────────────────────────────────────────────────────────────

class QuestionForm(forms.ModelForm):
    """
    Used in the HTMX panel of survey_detail.
    The mapped_to_co dropdown shows only COs for this survey's course.
    """
    class Meta:
        model  = Question
        fields = ['text', 'question_type', 'mapped_to_co', 'order', 'is_required']
        widgets = {
            'text' : forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, survey, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only COs for this survey's course
        self.fields['mapped_to_co'].queryset = CourseOutcome.objects.filter(
            course=survey.course
        )
        self.fields['mapped_to_co'].required = False
        self.fields['mapped_to_co'].label    = 'Linked Course Outcome (optional)'
        self.fields['order'].initial         = (
            survey.questions.count() + 1
        )

        for name, field in self.fields.items():
            if name == 'is_required':
                # Checkbox — don't apply text-input classes
                field.widget.attrs.update({'class': 'w-4 h-4 rounded border-slate-300 dark:border-dark-border text-primary focus:ring-primary dark:bg-dark-bg cursor-pointer'})
            else:
                existing = field.widget.attrs.get('class', '')
                field.widget.attrs['class'] = FIELD_CLASS + ' ' + existing
