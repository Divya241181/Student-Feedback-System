from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from .models import *

class FeedbackEndToEndTest(TestCase):
    def setUp(self):
        self.client = Client()

        # Create Faculty
        self.faculty_user = User.objects.create_user(username='faculty1', password='password123', first_name='John', last_name='Doe')
        self.faculty_prof = FacultyProfile.objects.create(user=self.faculty_user, employee_id='FAC001', department='CE')

        # Create Student
        self.student_user = User.objects.create_user(username='student1', password='password123', first_name='Jane', last_name='Smith')
        self.student_prof = StudentProfile.objects.create(
            user=self.student_user, enrollment_no='22CE001', branch='CE', semester=6, batch='2022'
        )

        # Create Course
        self.course = Course.objects.create(
            code='CS101', name='Intro to CS', credits=4, semester=6, batch='2022', faculty=self.faculty_prof
        )
        self.course.students.add(self.student_prof)

    def test_end_to_end_flow(self):
        # 1. Faculty Login
        response = self.client.post(reverse('login'), {'username': 'faculty1', 'password': 'password123'})
        self.assertRedirects(response, reverse('dashboard'), fetch_redirect_response=False)
        
        response = self.client.get(reverse('dashboard'))
        self.assertRedirects(response, reverse('faculty_dashboard'))

        # 2. Faculty Creates a Survey
        now = timezone.now()
        start = now - timedelta(days=1)
        end = now + timedelta(days=7)
        create_url = reverse('survey_create')
        response = self.client.post(create_url, {
            'title': 'Midterm Feedback',
            'course': self.course.pk,
            'start_date': start.strftime('%Y-%m-%d %H:%M'),
            'end_date': end.strftime('%Y-%m-%d %H:%M'),
        })
        self.assertRedirects(response, reverse('survey_detail', kwargs={'pk': 1}))
        self.assertTrue(Survey.objects.filter(title='Midterm Feedback').exists())
        survey = Survey.objects.get(title='Midterm Feedback')

        # 3. Faculty Adds Course Outcomes
        co_add_url = reverse('add_co', kwargs={'pk': survey.pk})
        response = self.client.post(co_add_url, {
            'code': 'CO1',
            'description': 'Understand basic computing.'
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(CourseOutcome.objects.filter(code='CO1').exists())
        co1 = CourseOutcome.objects.get(code='CO1')

        # 4. Faculty Adds Questions linked to CO
        q_add_url = reverse('add_question', kwargs={'pk': survey.pk})
        response = self.client.post(q_add_url, {
            'text': 'How was the course pace?',
            'question_type': 'rating',
            'order': 1,
            'is_required': True,
            'mapped_to_co': co1.pk
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Question.objects.filter(text='How was the course pace?').exists())
        question = Question.objects.get(text='How was the course pace?')

        # 5. Faculty Publishes Survey
        pub_url = reverse('publish_survey', kwargs={'pk': survey.pk})
        response = self.client.post(pub_url)
        self.assertRedirects(response, reverse('survey_detail', kwargs={'pk': survey.pk}))
        survey.refresh_from_db()
        self.assertTrue(survey.is_published)
        
        # Logout Faculty
        response = self.client.get(reverse('logout'))
        self.assertRedirects(response, reverse('login'))

        # 6. Student Login
        response = self.client.post(reverse('login'), {'username': 'student1', 'password': 'password123'})
        self.assertRedirects(response, reverse('dashboard'), fetch_redirect_response=False)
        
        response = self.client.get(reverse('dashboard'))
        self.assertRedirects(response, reverse('student_dashboard'))

        # 7. Student Takes Survey
        take_url = reverse('take_survey', kwargs={'pk': survey.pk})
        response = self.client.get(take_url)
        self.assertEqual(response.status_code, 200)

        # 8. Student Submits Survey
        submit_url = reverse('submit_survey', kwargs={'pk': survey.pk})
        response = self.client.post(submit_url, {
            f'question_{question.pk}': '5'
        })
        self.assertRedirects(response, reverse('student_dashboard'))
        self.assertEqual(SurveyResponse.objects.count(), 1)
        self.assertEqual(Answer.objects.filter(rating_value=5).count(), 1)

        # Logout Student
        self.client.get(reverse('logout'))

        # 9. Faculty Views Results
        self.client.post(reverse('login'), {'username': 'faculty1', 'password': 'password123'})
        results_url = reverse('survey_results', kwargs={'pk': survey.pk})
        response = self.client.get(results_url)
        self.assertEqual(response.status_code, 200)
        
        # Verify Context logic
        context = response.context
        self.assertEqual(context['total_responses'], 1)
        self.assertEqual(context['response_rate'], 100)
        self.assertTrue(context['has_co_data'])
        self.assertEqual(context['co_averages'][0]['avg'], 5.0)

        print("End-to-End Test successfully passed! Everything interacts perfectly.")
