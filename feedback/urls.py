from django.urls import path
from . import views

urlpatterns = [
    path('',                    views.home_redirect,      name='home'),
    path('login/',              views.login_view,          name='login'),
    path('logout/',             views.logout_view,         name='logout'),
    path('dashboard/',          views.dashboard_redirect,  name='dashboard'),

    # Faculty
    path('faculty/dashboard/',  views.faculty_dashboard,   name='faculty_dashboard'),

    # Student
    path('student/dashboard/',  views.student_dashboard,   name='student_dashboard'),

    # ── Survey management (faculty only) ──────────────────────────────────────
    path('survey/create/',                views.survey_create,    name='survey_create'),
    path('survey/<int:pk>/',              views.survey_detail,    name='survey_detail'),
    path('survey/<int:pk>/edit/',         views.survey_edit,      name='survey_edit'),
    path('survey/<int:pk>/delete/',       views.survey_delete,    name='survey_delete'),
    path('survey/<int:pk>/add-co/',       views.add_co,           name='add_co'),
    path('survey/<int:pk>/add-question/', views.add_question,     name='add_question'),
    path('survey/<int:survey_pk>/question/<int:question_pk>/edit/',   views.edit_question,   name='edit_question'),
    path('survey/<int:survey_pk>/question/<int:question_pk>/delete/', views.delete_question, name='delete_question'),
    path('survey/<int:pk>/publish/',      views.publish_survey,   name='publish_survey'),

    # ── Student: take and submit a survey ────────────────────────────────────
    path('survey/<int:pk>/take/',         views.take_survey,      name='take_survey'),
    path('survey/<int:pk>/submit/',       views.submit_survey,    name='submit_survey'),

    # ── Faculty: view results ─────────────────────────────────────────────────
    path('survey/<int:pk>/results/',      views.survey_results,   name='survey_results'),

    # ── Admin tools ───────────────────────────────────────────────────────────
    path('admin-panel/import/',           views.bulk_import,      name='bulk_import'),
]
