from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.db import transaction
from django.db.models import Avg, Count
import json

from .helpers import is_faculty, is_student
from .models import (Course, Survey, SurveyResponse, CourseOutcome,
                     Question, MCQOption, Answer, StudentProfile, FacultyProfile)
from .forms import SurveyForm, CourseOutcomeForm, QuestionForm


# ─────────────────────────────────────────────────────────────────────────────
# HOME REDIRECT
# ─────────────────────────────────────────────────────────────────────────────

def home_redirect(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('login')


# ─────────────────────────────────────────────────────────────────────────────
# LOGIN
# ─────────────────────────────────────────────────────────────────────────────

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password. Please try again.')

    return render(request, 'feedback/login.html')


# ─────────────────────────────────────────────────────────────────────────────
# LOGOUT
# ─────────────────────────────────────────────────────────────────────────────

def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')


# ─────────────────────────────────────────────────────────────────────────────
# DASHBOARD ROUTER
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def dashboard_redirect(request):
    user = request.user
    if user.is_superuser or user.is_staff:
        return redirect('/admin/')
    if is_faculty(user):
        return redirect('faculty_dashboard')
    if is_student(user):
        return redirect('student_dashboard')
    messages.error(request, 'Your account has not been assigned a role yet. Please contact the administrator.')
    logout(request)
    return redirect('login')


# ─────────────────────────────────────────────────────────────────────────────
# FACULTY DASHBOARD
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def faculty_dashboard(request):
    user = request.user
    if not is_faculty(user):
        messages.error(request, 'Access denied. This page is for faculty only.')
        return redirect('dashboard')

    faculty  = user.faculty_profile
    courses  = Course.objects.filter(faculty=faculty).prefetch_related('students').order_by('semester', 'code')
    course_ids = courses.values_list('id', flat=True)
    surveys  = Survey.objects.filter(course_id__in=course_ids).select_related('course').order_by('-start_date')
    
    drafts = []
    active_surveys = []
    closed_surveys = []
    
    for s in surveys:
        if not s.is_published:
            drafts.append(s)
        elif s.is_active():
            active_surveys.append(s)
        else:
            closed_surveys.append(s)

    context = {
        'faculty': faculty,
        'courses': courses,
        'drafts': drafts,
        'active_surveys': active_surveys,
        'closed_surveys': closed_surveys,
        'total_surveys_count': surveys.count(),
    }
    return render(request, 'feedback/faculty_dashboard.html', context)


# ─────────────────────────────────────────────────────────────────────────────
# STUDENT DASHBOARD
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def student_dashboard(request):
    user = request.user
    if not is_student(user):
        messages.error(request, 'Access denied. This page is for students only.')
        return redirect('dashboard')

    student          = user.student_profile
    enrolled_courses = student.enrolled_courses.all()
    course_ids       = enrolled_courses.values_list('id', flat=True)

    all_surveys = Survey.objects.filter(
        course_id__in=course_ids,
        is_published=True,
    ).select_related('course').order_by('-start_date')

    available_surveys = [s for s in all_surveys if s.is_active()]

    submitted_ids = set(
        SurveyResponse.objects.filter(
            student=student,
            survey__in=available_surveys
        ).values_list('survey_id', flat=True)
    )

    pending_surveys = [s for s in available_surveys if s.id not in submitted_ids]
    completed_surveys = [s for s in available_surveys if s.id in submitted_ids]

    context = {
        'student':           student,
        'enrolled_courses':  enrolled_courses,
        'pending_surveys':   pending_surveys,
        'completed_surveys': completed_surveys,
        'total_available':   len(available_surveys),
        'total_submitted':   len(submitted_ids),
    }
    return render(request, 'feedback/student_dashboard.html', context)


# ─────────────────────────────────────────────────────────────────────────────
# SURVEY CREATE
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def survey_create(request):
    if not is_faculty(request.user):
        messages.error(request, 'Only faculty can create surveys.')
        return redirect('dashboard')

    faculty = request.user.faculty_profile

    if request.method == 'POST':
        form = SurveyForm(faculty, request.POST)
        if form.is_valid():
            survey = form.save()
            messages.success(request, f'Survey "{survey.title}" created! Now add COs and questions.')
            return redirect('survey_detail', pk=survey.pk)
    else:
        form = SurveyForm(faculty)

    return render(request, 'feedback/survey_create.html', {'form': form})


# ─────────────────────────────────────────────────────────────────────────────
# SURVEY DETAIL
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def survey_detail(request, pk):
    survey = get_object_or_404(Survey, pk=pk)

    if not is_faculty(request.user):
        messages.error(request, 'Only faculty can access the survey builder.')
        return redirect('dashboard')

    if survey.course.faculty != request.user.faculty_profile:
        messages.error(request, 'You do not own this survey.')
        return redirect('faculty_dashboard')

    cos       = CourseOutcome.objects.filter(course=survey.course).order_by('code')
    questions = survey.questions.select_related('mapped_to_co').order_by('order')
    co_form   = CourseOutcomeForm()
    q_form    = QuestionForm(survey)

    context = {
        'survey':    survey,
        'cos':       cos,
        'questions': questions,
        'co_form':   co_form,
        'q_form':    q_form,
        'survey_has_responses': survey.responses.exists(),
    }
    return render(request, 'feedback/survey_detail.html', context)


# ─────────────────────────────────────────────────────────────────────────────
# SURVEY EDIT & DELETE
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def survey_edit(request, pk):
    survey = get_object_or_404(Survey, pk=pk)

    if not is_faculty(request.user):
        messages.error(request, 'Only faculty can edit surveys.')
        return redirect('dashboard')

    if survey.course.faculty != request.user.faculty_profile:
        messages.error(request, 'You do not own this survey.')
        return redirect('faculty_dashboard')

    if request.method == 'POST':
        form = SurveyForm(request.user.faculty_profile, request.POST, instance=survey)
        if form.is_valid():
            survey = form.save()
            messages.success(request, f'Survey "{survey.title}" has been updated.')
            return redirect('survey_detail', pk=survey.pk)
    else:
        form = SurveyForm(request.user.faculty_profile, instance=survey)

    return render(request, 'feedback/survey_create.html', {
        'form': form,
        'is_edit': True,
        'survey': survey
    })

@login_required
def survey_delete(request, pk):
    survey = get_object_or_404(Survey, pk=pk)

    if not is_faculty(request.user):
        return HttpResponse('Unauthorized', status=403)

    if survey.course.faculty != request.user.faculty_profile:
        messages.error(request, 'You do not own this survey.')
        return redirect('faculty_dashboard')

    if request.method == 'POST':
        title = survey.title
        survey.delete()
        messages.success(request, f'Survey "{title}" and all its related data have been permanently deleted.')
        return redirect('faculty_dashboard')
    
    return redirect('faculty_dashboard')


# ─────────────────────────────────────────────────────────────────────────────
# ADD COURSE OUTCOME  (HTMX)
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def add_co(request, pk):
    survey = get_object_or_404(Survey, pk=pk)

    if not is_faculty(request.user):
        return HttpResponse('Unauthorized', status=403)

    if request.method == 'POST':
        form = CourseOutcomeForm(request.POST)
        if form.is_valid():
            co        = form.save(commit=False)
            co.course = survey.course
            co.save()

    cos = CourseOutcome.objects.filter(course=survey.course).order_by('code')
    return render(request, 'feedback/partials/co_list.html', {
        'cos': cos,
        'survey': survey,
        'survey_has_responses': survey.responses.exists()
    })


# ─────────────────────────────────────────────────────────────────────────────
# ADD QUESTION  (HTMX)
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def add_question(request, pk):
    survey = get_object_or_404(Survey, pk=pk)

    if not is_faculty(request.user):
        return HttpResponse('Unauthorized', status=403)

    if request.method == 'POST':
        form = QuestionForm(survey, request.POST)
        if form.is_valid():
            question        = form.save(commit=False)
            question.survey = survey
            question.save()

            if question.question_type == Question.MCQ:
                options = request.POST.getlist('mcq_options')
                order_idx = 1
                for opt_text in options:
                    opt_text = opt_text.strip()
                    if opt_text:
                        MCQOption.objects.create(question=question, option_text=opt_text, order=order_idx)
                        order_idx += 1

    questions = survey.questions.select_related('mapped_to_co').order_by('order')
    return render(request, 'feedback/partials/question_list.html', {
        'questions': questions,
        'survey': survey,
        'survey_has_responses': survey.responses.exists()
    })

# ─────────────────────────────────────────────────────────────────────────────
# EDIT QUESTION  (HTMX)
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def edit_question(request, survey_pk, question_pk):
    survey = get_object_or_404(Survey, pk=survey_pk)
    question = get_object_or_404(Question, pk=question_pk, survey=survey)

    if not is_faculty(request.user) or survey.course.faculty != request.user.faculty_profile:
        return HttpResponse('Unauthorized', status=403)

    if survey.responses.exists():
        return HttpResponse("Cannot edit questions with existing responses.", status=403)

    if request.method == 'POST':
        form = QuestionForm(survey, request.POST, instance=question)
        if form.is_valid():
            question = form.save()
            
            if question.question_type == Question.MCQ:
                options = request.POST.getlist('mcq_options')
                question.mcq_options.all().delete()
                order_idx = 1
                for opt_text in options:
                    opt_text = opt_text.strip()
                    if opt_text:
                        MCQOption.objects.create(question=question, option_text=opt_text, order=order_idx)
                        order_idx += 1
            else:
                question.mcq_options.all().delete()
                
            questions = survey.questions.select_related('mapped_to_co').order_by('order')
            return render(request, 'feedback/partials/question_list.html', {
                'questions': questions,
                'survey': survey,
                'survey_has_responses': survey.responses.exists()
            })
    else:
        form = QuestionForm(survey, instance=question)

    return render(request, 'feedback/partials/question_edit_form.html', {
        'q_form': form,
        'q': question,
        'survey': survey
    })

# ─────────────────────────────────────────────────────────────────────────────
# DELETE QUESTION  (HTMX)
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def delete_question(request, survey_pk, question_pk):
    survey = get_object_or_404(Survey, pk=survey_pk)
    question = get_object_or_404(Question, pk=question_pk, survey=survey)

    if not is_faculty(request.user) or survey.course.faculty != request.user.faculty_profile:
        return HttpResponse('Unauthorized', status=403)

    if survey.responses.exists():
        return HttpResponse("Cannot delete questions with existing responses.", status=403)

    if request.method in ['POST', 'DELETE']:
        question.delete()
        questions = survey.questions.select_related('mapped_to_co').order_by('order')
        return render(request, 'feedback/partials/question_list.html', {
            'questions': questions,
            'survey': survey,
            'survey_has_responses': survey.responses.exists()
        })
    return HttpResponse('Method not allowed', status=405)


# ─────────────────────────────────────────────────────────────────────────────
# PUBLISH SURVEY
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def publish_survey(request, pk):
    survey = get_object_or_404(Survey, pk=pk)

    if not is_faculty(request.user):
        messages.error(request, 'Only faculty can publish surveys.')
        return redirect('dashboard')

    if survey.course.faculty != request.user.faculty_profile:
        messages.error(request, 'You do not own this survey.')
        return redirect('faculty_dashboard')

    if request.method == 'POST':
        survey.is_published = not survey.is_published
        survey.save()
        state = 'published' if survey.is_published else 'unpublished'
        messages.success(request, f'Survey "{survey.title}" has been {state}.')

    return redirect('survey_detail', pk=survey.pk)


# ─────────────────────────────────────────────────────────────────────────────
# TAKE SURVEY
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def take_survey(request, pk):
    survey = get_object_or_404(Survey, pk=pk)

    if not is_student(request.user):
        messages.error(request, 'Only students can fill surveys.')
        return redirect('dashboard')

    student = request.user.student_profile

    if not survey.is_active():
        messages.error(request, 'This survey is not currently open.')
        return redirect('student_dashboard')

    if not student.enrolled_courses.filter(pk=survey.course.pk).exists():
        messages.error(request, 'You are not enrolled in this course.')
        return redirect('student_dashboard')

    if SurveyResponse.objects.filter(survey=survey, student=student).exists():
        messages.warning(request, 'You have already submitted this survey.')
        return redirect('student_dashboard')

    questions = (
        survey.questions
        .select_related('mapped_to_co')
        .prefetch_related('mcq_options')
        .order_by('order')
    )

    context = {
        'survey':    survey,
        'student':   student,
        'questions': questions,
    }
    return render(request, 'feedback/take_survey.html', context)


# ─────────────────────────────────────────────────────────────────────────────
# SUBMIT SURVEY
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def submit_survey(request, pk):
    survey = get_object_or_404(Survey, pk=pk)

    if not is_student(request.user):
        messages.error(request, 'Only students can submit surveys.')
        return redirect('dashboard')

    if request.method != 'POST':
        return redirect('take_survey', pk=pk)

    student = request.user.student_profile

    if not survey.is_active():
        messages.error(request, 'This survey is no longer accepting responses.')
        return redirect('student_dashboard')

    if not student.enrolled_courses.filter(pk=survey.course.pk).exists():
        messages.error(request, 'You are not enrolled in this course.')
        return redirect('student_dashboard')

    if SurveyResponse.objects.filter(survey=survey, student=student).exists():
        messages.warning(request, 'You have already submitted this survey.')
        return redirect('student_dashboard')

    questions = survey.questions.select_related('mapped_to_co').order_by('order')

    errors = []
    for question in questions:
        raw = request.POST.get(f'question_{question.pk}', '').strip()
        if question.is_required and not raw:
            errors.append(f'Question {question.order} is required.')

    if errors:
        messages.error(request, 'Please answer all required questions.')
        questions = (
            survey.questions
            .select_related('mapped_to_co')
            .prefetch_related('mcq_options')
            .order_by('order')
        )
        return render(request, 'feedback/take_survey.html', {
            'survey':    survey,
            'student':   student,
            'questions': questions,
            'errors':    errors,
        })

    try:
        with transaction.atomic():
            response = SurveyResponse.objects.create(survey=survey, student=student)

            for question in questions:
                raw = request.POST.get(f'question_{question.pk}', '').strip()

                if not raw and not question.is_required:
                    continue

                answer = Answer(response=response, question=question)

                if question.question_type == Question.RATING:
                    try:
                        val = int(raw)
                        answer.rating_value = max(1, min(5, val))
                    except (ValueError, TypeError):
                        answer.rating_value = None

                elif question.question_type == Question.TEXT:
                    answer.text_value = raw

                elif question.question_type == Question.MCQ:
                    try:
                        option = MCQOption.objects.get(pk=int(raw), question=question)
                        answer.mcq_choice = option
                    except (MCQOption.DoesNotExist, ValueError):
                        pass

                elif question.question_type == Question.YES_NO:
                    answer.yes_no_value = (raw.lower() in ('yes', 'true', '1'))

                answer.save()

    except Exception:
        messages.error(request, 'Submission failed. You may have already submitted this survey.')
        return redirect('student_dashboard')

    messages.success(request, f'Thank you! Your feedback for "{survey.title}" has been submitted.')
    return redirect('student_dashboard')


# ─────────────────────────────────────────────────────────────────────────────
# SURVEY RESULTS
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def survey_results(request, pk):
    survey = get_object_or_404(Survey, pk=pk)

    if not is_faculty(request.user):
        messages.error(request, 'Only faculty can view results.')
        return redirect('dashboard')

    if survey.course.faculty != request.user.faculty_profile:
        messages.error(request, "You do not have access to this survey's results.")
        return redirect('faculty_dashboard')

    total_responses = survey.responses.count()
    total_students  = survey.course.students.count()
    response_rate   = round((total_responses / total_students) * 100) if total_students > 0 else 0

    cos         = CourseOutcome.objects.filter(course=survey.course).order_by('code')
    co_averages = []

    for co in cos:
        avg = Answer.objects.filter(
            response__survey=survey,
            question__mapped_to_co=co,
            rating_value__isnull=False,
        ).aggregate(avg=Avg('rating_value'))['avg']
        co_averages.append({
            'code': co.code,
            'desc': co.description[:70],
            'avg':  round(avg, 2) if avg else 0,
        })

    question_stats   = []
    rating_questions = (
        survey.questions
        .filter(question_type=Question.RATING)
        .select_related('mapped_to_co')
        .order_by('order')
    )

    for q in rating_questions:
        avg = Answer.objects.filter(
            response__survey=survey,
            question=q,
            rating_value__isnull=False,
        ).aggregate(avg=Avg('rating_value'))['avg']

        ans_count = Answer.objects.filter(
            response__survey=survey,
            question=q,
            rating_value__isnull=False,
        ).count()

        question_stats.append({
            'text':  q.text,
            'co':    q.mapped_to_co.code if q.mapped_to_co else '—',
            'avg':   round(avg, 2) if avg else 0,
            'count': ans_count,
            'pct':   round((avg / 5) * 100) if avg else 0,
        })

    open_answers = (
        Answer.objects
        .filter(
            response__survey=survey,
            question__question_type=Question.TEXT,
            text_value__gt='',
        )
        .select_related('question', 'response', 'response__student', 'response__student__user')
        .order_by('question__order')
    )

    mcq_questions = (
        survey.questions
        .filter(question_type=Question.MCQ)
        .prefetch_related('mcq_options')
        .order_by('order')
    )
    mcq_stats = []
    for q in mcq_questions:
        option_counts = []
        for opt in q.mcq_options.all():
            count = Answer.objects.filter(response__survey=survey, mcq_choice=opt).count()
            option_counts.append({'option': opt.option_text, 'count': count})
        mcq_stats.append({'question': q.text, 'options': option_counts})

    co_labels = json.dumps([c['code'] for c in co_averages])
    co_data   = json.dumps([c['avg']  for c in co_averages])
    co_descs  = json.dumps([c['desc'] for c in co_averages])

    has_co_data = any(c['avg'] > 0 for c in co_averages)

    context = {
        'survey':          survey,
        'total_responses': total_responses,
        'total_students':  total_students,
        'response_rate':   response_rate,
        'has_co_data':     has_co_data,
        'co_averages':     co_averages,
        'question_stats':  question_stats,
        'open_answers':    open_answers,
        'mcq_stats':       mcq_stats,
        'co_labels':       co_labels,
        'co_data':         co_data,
        'co_descs':        co_descs,
    }
    return render(request, 'feedback/survey_results.html', context)


# ─────────────────────────────────────────────────────────────────────────────
# BULK IMPORT  — Students, Faculty, AND Courses
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def bulk_import(request):
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Only administrators can access the bulk import tool.')
        return redirect('dashboard')

    import_results = None

    if request.method == 'POST':
        import_type = request.POST.get('import_type', 'students')
        csv_file    = request.FILES.get('csv_file')

        if not csv_file:
            messages.error(request, 'Please select a CSV file to upload.')
            return render(request, 'feedback/bulk_import.html')

        if not csv_file.name.endswith('.csv'):
            messages.error(request, 'Only .csv files are accepted.')
            return render(request, 'feedback/bulk_import.html')

        import csv
        import io
        from django.contrib.auth.models import User

        try:
            decoded = csv_file.read().decode('utf-8-sig')
        except UnicodeDecodeError:
            messages.error(request, 'File encoding error. Please save as UTF-8 CSV.')
            return render(request, 'feedback/bulk_import.html')

        reader  = csv.reader(io.StringIO(decoded))
        created = 0
        skipped = 0
        errors  = []

        for row_num, row in enumerate(reader, start=1):
            # Skip header row and blank rows
            if not row or row[0].strip().lower() in ('first_name', 'code', ''):
                continue

            try:
                row = [cell.strip() for cell in row]

                # ── STUDENTS ──────────────────────────────────────────────────
                if import_type == 'students':
                    if len(row) < 8:
                        errors.append(f'Row {row_num}: needs 8 columns, got {len(row)}')
                        continue

                    first_name, last_name, username, password, \
                    enrollment_no, branch, semester, batch = row[:8]

                    if User.objects.filter(username=username).exists():
                        skipped += 1
                        continue

                    user = User.objects.create_user(
                        username=username, password=password,
                        first_name=first_name, last_name=last_name,
                    )
                    StudentProfile.objects.create(
                        user=user, enrollment_no=enrollment_no,
                        branch=branch, semester=int(semester), batch=batch,
                    )
                    created += 1

                # ── FACULTY ───────────────────────────────────────────────────
                elif import_type == 'faculty':
                    if len(row) < 7:
                        errors.append(f'Row {row_num}: needs 7 columns, got {len(row)}')
                        continue

                    first_name, last_name, username, password, \
                    employee_id, department, designation = row[:7]

                    if User.objects.filter(username=username).exists():
                        skipped += 1
                        continue

                    user = User.objects.create_user(
                        username=username, password=password,
                        first_name=first_name, last_name=last_name,
                    )
                    FacultyProfile.objects.create(
                        user=user, employee_id=employee_id,
                        department=department, designation=designation,
                    )
                    created += 1

                # ── COURSES ───────────────────────────────────────────────────
                elif import_type == 'courses':
                    # CSV columns: code, name, credits, semester, batch, faculty_employee_id
                    if len(row) < 6:
                        errors.append(f'Row {row_num}: needs 6 columns, got {len(row)}')
                        continue

                    code, name, credits, semester, batch, faculty_employee_id = row[:6]

                    # Skip if course code already exists
                    if Course.objects.filter(code=code).exists():
                        skipped += 1
                        continue

                    # Find the faculty by employee_id
                    try:
                        faculty = FacultyProfile.objects.get(employee_id=faculty_employee_id)
                    except FacultyProfile.DoesNotExist:
                        errors.append(
                            f'Row {row_num}: Faculty with Employee ID "{faculty_employee_id}" not found. '
                            f'Import faculty first.'
                        )
                        continue

                    Course.objects.create(
                        code=code,
                        name=name,
                        credits=int(credits),
                        semester=int(semester),
                        batch=batch,
                        faculty=faculty,
                    )
                    created += 1

            except ValueError as e:
                errors.append(f'Row {row_num}: invalid value — {e}')
            except Exception as e:
                errors.append(f'Row {row_num}: unexpected error — {e}')

        import_results = {
            'created': created,
            'skipped': skipped,
            'errors':  errors,
        }

        if created:
            messages.success(request, f'Import complete: {created} record(s) created.')
        if skipped:
            messages.warning(request, f'{skipped} row(s) skipped (already exists).')

    return render(request, 'feedback/bulk_import.html', {
        'import_results': import_results,
    })
