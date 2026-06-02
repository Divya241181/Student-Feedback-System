from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='FacultyProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('employee_id', models.CharField(help_text='College-assigned employee ID, e.g. FAC001', max_length=20, unique=True)),
                ('department', models.CharField(max_length=100)),
                ('designation', models.CharField(blank=True, help_text='e.g. Assistant Professor, HOD', max_length=100)),
                ('phone', models.CharField(blank=True, max_length=15)),
                ('profile_pic', models.ImageField(blank=True, null=True, upload_to='faculty_pics/')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='faculty_profile', to=settings.AUTH_USER_MODEL)),
            ],
            options={'verbose_name': 'Faculty Profile', 'verbose_name_plural': 'Faculty Profiles'},
        ),
        migrations.CreateModel(
            name='StudentProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('enrollment_no', models.CharField(help_text='e.g. 22CE001', max_length=20, unique=True)),
                ('branch', models.CharField(help_text='e.g. Computer Engineering', max_length=100)),
                ('semester', models.PositiveSmallIntegerField(help_text='Current semester: 1–8')),
                ('batch', models.CharField(help_text='e.g. 2022-26', max_length=10)),
                ('phone', models.CharField(blank=True, max_length=15)),
                ('profile_pic', models.ImageField(blank=True, null=True, upload_to='student_pics/')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='student_profile', to=settings.AUTH_USER_MODEL)),
            ],
            options={'verbose_name': 'Student Profile', 'verbose_name_plural': 'Student Profiles'},
        ),
        migrations.CreateModel(
            name='Course',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(help_text='e.g. CE301', max_length=20, unique=True)),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('credits', models.PositiveSmallIntegerField(default=4)),
                ('semester', models.PositiveSmallIntegerField()),
                ('batch', models.CharField(help_text='e.g. 2022-26', max_length=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('faculty', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='courses_taught', to='feedback.facultyprofile')),
                ('students', models.ManyToManyField(blank=True, related_name='enrolled_courses', to='feedback.studentprofile')),
            ],
            options={'verbose_name': 'Course', 'verbose_name_plural': 'Courses', 'ordering': ['semester', 'code']},
        ),
        migrations.CreateModel(
            name='CourseOutcome',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(help_text='e.g. CO1, CO2', max_length=10)),
                ('description', models.TextField(help_text='What the student will be able to do after this course')),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='course_outcomes', to='feedback.course')),
            ],
            options={'verbose_name': 'Course Outcome', 'verbose_name_plural': 'Course Outcomes', 'ordering': ['course', 'code'], 'unique_together': {('course', 'code')}},
        ),
        migrations.CreateModel(
            name='Survey',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('start_date', models.DateTimeField()),
                ('end_date', models.DateTimeField()),
                ('is_published', models.BooleanField(default=False, help_text='Only published surveys are visible to students')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='surveys', to='feedback.course')),
            ],
            options={'verbose_name': 'Survey', 'verbose_name_plural': 'Surveys', 'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField(help_text='The question as the student will read it')),
                ('question_type', models.CharField(choices=[('rating', 'Rating (1–5)'), ('text', 'Open Text'), ('mcq', 'Multiple Choice'), ('yes_no', 'Yes / No')], default='rating', max_length=10)),
                ('order', models.PositiveSmallIntegerField(default=0, help_text='Display order within the survey')),
                ('is_required', models.BooleanField(default=True)),
                ('survey', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='questions', to='feedback.survey')),
                ('mapped_to_co', models.ForeignKey(blank=True, help_text='Optional: link to a Course Outcome for OBE reports', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='questions', to='feedback.courseoutcome')),
            ],
            options={'verbose_name': 'Question', 'verbose_name_plural': 'Questions', 'ordering': ['survey', 'order']},
        ),
        migrations.CreateModel(
            name='MCQOption',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('option_text', models.CharField(max_length=255)),
                ('order', models.PositiveSmallIntegerField(default=0)),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='mcq_options', to='feedback.question')),
            ],
            options={'verbose_name': 'MCQ Option', 'verbose_name_plural': 'MCQ Options', 'ordering': ['question', 'order']},
        ),
        migrations.CreateModel(
            name='SurveyResponse',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('submitted_at', models.DateTimeField(auto_now_add=True)),
                ('is_anonymous', models.BooleanField(default=False)),
                ('survey', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='responses', to='feedback.survey')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='survey_responses', to='feedback.studentprofile')),
            ],
            options={'verbose_name': 'Survey Response', 'verbose_name_plural': 'Survey Responses', 'ordering': ['-submitted_at'], 'unique_together': {('survey', 'student')}},
        ),
        migrations.CreateModel(
            name='Answer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rating_value', models.PositiveSmallIntegerField(blank=True, help_text='1–5 for RATING questions', null=True)),
                ('text_value', models.TextField(blank=True, help_text='Free text for TEXT questions')),
                ('yes_no_value', models.BooleanField(blank=True, help_text='True/False for YES_NO questions', null=True)),
                ('response', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='answers', to='feedback.surveyresponse')),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='answers', to='feedback.question')),
                ('mcq_choice', models.ForeignKey(blank=True, help_text='Selected option for MCQ questions', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='chosen_answers', to='feedback.mcqoption')),
            ],
            options={'verbose_name': 'Answer', 'verbose_name_plural': 'Answers', 'unique_together': {('response', 'question')}},
        ),
    ]
