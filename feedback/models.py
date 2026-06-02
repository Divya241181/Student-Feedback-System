"""
feedback/models.py
==================
This file defines the full data model for the College Feedback System.

The 9 models here form the backbone of the entire application:

    FacultyProfile  ← extends Django's built-in User for teachers
    StudentProfile  ← extends Django's built-in User for students
    Course          ← a subject taught by a faculty member
    Survey          ← a feedback form tied to a course, with a deadline
    CourseOutcome   ← CO1, CO2, ... mapped to a course
    Question        ← a question inside a survey (text, rating, MCQ, etc.)
    MCQOption       ← the choices for an MCQ question
    SurveyResponse  ← one student's submission of an entire survey
    Answer          ← one student's answer to one question inside a response

Why extend User instead of replacing it?
  Django's built-in User gives us login, password hashing, sessions, and
  admin integration for free. We just "hang" extra info off it via a
  OneToOneField — the classic "profile" pattern.
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


# ─────────────────────────────────────────────────────────────────────────────
# PROFILE MODELS
# ─────────────────────────────────────────────────────────────────────────────

class FacultyProfile(models.Model):
    """
    Extra info for a User who is a faculty member.

    OneToOneField means: one User ↔ one FacultyProfile.
    on_delete=CASCADE means: if the User is deleted, this profile is deleted too.
    """
    user         = models.OneToOneField(User, on_delete=models.CASCADE,
                                        related_name='faculty_profile')
    employee_id  = models.CharField(max_length=20, unique=True,
                                    help_text="College-assigned employee ID, e.g. FAC001")
    department   = models.CharField(max_length=100)
    designation  = models.CharField(max_length=100, blank=True,
                                    help_text="e.g. Assistant Professor, HOD")
    phone        = models.CharField(max_length=15, blank=True)
    # blank=True → optional; upload_to tells Django where inside MEDIA_ROOT to save files
    profile_pic  = models.ImageField(upload_to='faculty_pics/', blank=True, null=True)

    class Meta:
        verbose_name        = "Faculty Profile"
        verbose_name_plural = "Faculty Profiles"

    def __str__(self):
        # Django admin and dropdowns will show: "Dr. Smith (FAC001)"
        return f"{self.user.get_full_name()} ({self.employee_id})"


class StudentProfile(models.Model):
    """
    Extra info for a User who is a student.
    """
    user         = models.OneToOneField(User, on_delete=models.CASCADE,
                                        related_name='student_profile')
    enrollment_no = models.CharField(max_length=20, unique=True,
                                     help_text="e.g. 22CE001")
    branch       = models.CharField(max_length=100, help_text="e.g. Computer Engineering")
    semester     = models.PositiveSmallIntegerField(help_text="Current semester: 1–8")
    batch        = models.CharField(max_length=10, help_text="e.g. 2022-26")
    phone        = models.CharField(max_length=15, blank=True)
    profile_pic  = models.ImageField(upload_to='student_pics/', blank=True, null=True)

    class Meta:
        verbose_name        = "Student Profile"
        verbose_name_plural = "Student Profiles"

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.enrollment_no})"


# ─────────────────────────────────────────────────────────────────────────────
# COURSE
# ─────────────────────────────────────────────────────────────────────────────

class Course(models.Model):
    """
    A subject taught by a faculty member in a given semester/year.

    ManyToManyField for students: one student is enrolled in many courses;
    one course has many students. Django creates the join table automatically.
    """
    code        = models.CharField(max_length=20, unique=True,
                                   help_text="e.g. CE301")
    name        = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    credits     = models.PositiveSmallIntegerField(default=4)
    semester    = models.PositiveSmallIntegerField()
    batch       = models.CharField(max_length=10, help_text="e.g. 2022-26")

    # ForeignKey: many courses can be taught by one faculty.
    # SET_NULL: if a faculty is deleted, their courses remain (faculty=null).
    faculty     = models.ForeignKey(FacultyProfile, on_delete=models.SET_NULL,
                                    null=True, related_name='courses_taught')
    students    = models.ManyToManyField(StudentProfile, blank=True,
                                         related_name='enrolled_courses')
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = "Course"
        verbose_name_plural = "Courses"
        ordering            = ['semester', 'code']

    def __str__(self):
        return f"{self.code} – {self.name}"


# ─────────────────────────────────────────────────────────────────────────────
# SURVEY
# ─────────────────────────────────────────────────────────────────────────────

class Survey(models.Model):
    """
    A feedback form associated with one Course.

    Key design decisions:
    - A survey has a start_date and end_date; is_active() checks both.
    - is_published controls whether students can *see* the survey at all
      (an admin might prepare a survey in advance before publishing it).
    """
    title        = models.CharField(max_length=200)
    description  = models.TextField(blank=True)
    course       = models.ForeignKey(Course, on_delete=models.CASCADE,
                                     related_name='surveys')
    start_date   = models.DateTimeField()
    end_date     = models.DateTimeField()
    is_published = models.BooleanField(default=False,
                                       help_text="Only published surveys are visible to students")
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "Survey"
        verbose_name_plural = "Surveys"
        ordering            = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.course.code})"

    def is_active(self):
        """
        Returns True only if:
          1. The survey is published (admin flipped the switch), AND
          2. Current time is between start_date and end_date.

        This is why we store both flags. A survey can be published but
        expired (past end_date), or active-window but not yet published.
        Only when BOTH conditions are true should students be able to submit.
        """
        now = timezone.now()
        return self.is_published and (self.start_date <= now <= self.end_date)

    # Make is_active behave nicely in Django admin (shows ✓/✗ icon)
    is_active.boolean = True


# ─────────────────────────────────────────────────────────────────────────────
# COURSE OUTCOME
# ─────────────────────────────────────────────────────────────────────────────

class CourseOutcome(models.Model):
    """
    CO1, CO2, ... for a given Course.

    In outcome-based education (OBE), each course has 4–6 measurable
    outcomes. Questions in a survey can be mapped to these outcomes so
    reports can show "CO attainment levels".
    """
    course      = models.ForeignKey(Course, on_delete=models.CASCADE,
                                    related_name='course_outcomes')
    code        = models.CharField(max_length=10, help_text="e.g. CO1, CO2")
    description = models.TextField(help_text="What the student will be able to do after this course")

    class Meta:
        verbose_name        = "Course Outcome"
        verbose_name_plural = "Course Outcomes"
        unique_together     = ('course', 'code')   # CO1 should be unique per course
        ordering            = ['course', 'code']

    def __str__(self):
        return f"{self.course.code} – {self.code}"


# ─────────────────────────────────────────────────────────────────────────────
# QUESTION
# ─────────────────────────────────────────────────────────────────────────────

class Question(models.Model):
    """
    A single question inside a Survey.

    question_type determines how the frontend renders it and how answers
    are interpreted:
      - RATING   → 1–5 star or numeric scale (stored as a number)
      - TEXT      → open-ended text box
      - MCQ       → multiple-choice (options in MCQOption table)
      - YES_NO    → simple boolean choice

    mapped_to_co is optional: link a question to a CourseOutcome so the
    system can calculate CO attainment from rating answers.
    """
    RATING  = 'rating'
    TEXT    = 'text'
    MCQ     = 'mcq'
    YES_NO  = 'yes_no'

    QUESTION_TYPE_CHOICES = [
        (RATING,  'Rating (1–5)'),
        (TEXT,    'Open Text'),
        (MCQ,     'Multiple Choice'),
        (YES_NO,  'Yes / No'),
    ]

    survey         = models.ForeignKey(Survey, on_delete=models.CASCADE,
                                       related_name='questions')
    text           = models.TextField(help_text="The question as the student will read it")
    question_type  = models.CharField(max_length=10, choices=QUESTION_TYPE_CHOICES,
                                      default=RATING)
    order          = models.PositiveSmallIntegerField(default=0,
                                                      help_text="Display order within the survey")
    is_required    = models.BooleanField(default=True)
    mapped_to_co   = models.ForeignKey(CourseOutcome, on_delete=models.SET_NULL,
                                       null=True, blank=True,
                                       related_name='questions',
                                       help_text="Optional: link to a Course Outcome for OBE reports")

    class Meta:
        verbose_name        = "Question"
        verbose_name_plural = "Questions"
        ordering            = ['survey', 'order']

    def __str__(self):
        return f"[{self.get_question_type_display()}] {self.text[:60]}"


# ─────────────────────────────────────────────────────────────────────────────
# MCQ OPTION
# ─────────────────────────────────────────────────────────────────────────────

class MCQOption(models.Model):
    """
    One choice for an MCQ Question.

    Example: Question = "Which teaching method was most effective?"
             Options  = ["Lecture", "Group Discussion", "Lab Work", "Case Study"]

    Keeping options in a separate table (rather than a JSON field) makes it
    easy to count how many students chose each option for analytics.
    """
    question   = models.ForeignKey(Question, on_delete=models.CASCADE,
                                   related_name='mcq_options')
    option_text = models.CharField(max_length=255)
    order       = models.PositiveSmallIntegerField(default=0)

    class Meta:
        verbose_name        = "MCQ Option"
        verbose_name_plural = "MCQ Options"
        ordering            = ['question', 'order']

    def __str__(self):
        return f"{self.question.text[:40]} → {self.option_text}"


# ─────────────────────────────────────────────────────────────────────────────
# SURVEY RESPONSE
# ─────────────────────────────────────────────────────────────────────────────

class SurveyResponse(models.Model):
    """
    One student's complete submission of a Survey.

    unique_together ensures a student can only submit once per survey.
    Individual answers are stored in the Answer model (one row per question).

    is_anonymous: if True, the student's identity should not be shown
    in faculty reports — only admin can see the full data.
    """
    survey       = models.ForeignKey(Survey, on_delete=models.CASCADE,
                                     related_name='responses')
    student      = models.ForeignKey(StudentProfile, on_delete=models.CASCADE,
                                     related_name='survey_responses')
    submitted_at = models.DateTimeField(auto_now_add=True)
    is_anonymous = models.BooleanField(default=False)

    class Meta:
        verbose_name        = "Survey Response"
        verbose_name_plural = "Survey Responses"
        # Prevents double submissions by the same student
        unique_together     = ('survey', 'student')
        ordering            = ['-submitted_at']

    def __str__(self):
        return f"{self.student} → {self.survey} ({self.submitted_at.date()})"


# ─────────────────────────────────────────────────────────────────────────────
# ANSWER
# ─────────────────────────────────────────────────────────────────────────────

class Answer(models.Model):
    """
    One student's answer to one Question within a SurveyResponse.

    We store all answer types in one table using nullable fields:
      - rating_value  → filled for RATING questions (1–5)
      - text_value    → filled for TEXT questions
      - mcq_choice    → filled for MCQ questions (points to chosen MCQOption)
      - yes_no_value  → filled for YES_NO questions

    Why not separate tables per type? Because queries like
    "show all answers for this survey" become simple; you just filter
    by response and check which field is non-null for the type.
    """
    response    = models.ForeignKey(SurveyResponse, on_delete=models.CASCADE,
                                    related_name='answers')
    question    = models.ForeignKey(Question, on_delete=models.CASCADE,
                                    related_name='answers')

    # Only ONE of these should be filled, depending on question type
    rating_value  = models.PositiveSmallIntegerField(
                        null=True, blank=True,
                        help_text="1–5 for RATING questions")
    text_value    = models.TextField(
                        blank=True,
                        help_text="Free text for TEXT questions")
    mcq_choice    = models.ForeignKey(
                        MCQOption, on_delete=models.SET_NULL,
                        null=True, blank=True,
                        related_name='chosen_answers',
                        help_text="Selected option for MCQ questions")
    yes_no_value  = models.BooleanField(
                        null=True, blank=True,
                        help_text="True/False for YES_NO questions")

    class Meta:
        verbose_name        = "Answer"
        verbose_name_plural = "Answers"
        # One answer per question per response — no duplicates
        unique_together     = ('response', 'question')

    def __str__(self):
        return f"Answer to '{self.question.text[:40]}'"
