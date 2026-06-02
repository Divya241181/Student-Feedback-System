# Student Feedback System

A **College Feedback & OBE (Outcome-Based Education) Management System** built with **Django** — featuring separate Faculty and Student portals, a drag-and-drop survey builder, Course Outcome (CO) analytics, and bulk CSV import.

---

## ✨ Features

### 👨‍🏫 Faculty Portal
- **Dashboard** — view assigned courses, draft/active/closed surveys at a glance
- **Survey Builder** — create surveys with Rating (1–5), MCQ, Open Text, and Yes/No questions
- **Course Outcomes (CO)** — map questions to CO1, CO2… for OBE reports
- **Analytics** — response rates, CO achievement bar chart (Chart.js), question-level breakdown, open responses
- **Publish/Unpublish** control with editing lock once students have responded

### 🎓 Student Portal
- **Dashboard** — pending surveys with countdown, completed feedback history
- **Take Survey** — sticky progress bar, interactive rating buttons, custom MCQ & Yes/No inputs
- Anonymous submission support

### 🔧 Admin Features
- **Bulk Import** — upload CSV to create Students, Faculty, or Courses all at once
- Django admin panel for full data management

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 4.x (Python) |
| Database | SQLite (dev) |
| Frontend | Tailwind CSS (CDN), Alpine.js, HTMX, Chart.js |
| Fonts | Plus Jakarta Sans, Inter, JetBrains Mono |
| Auth | Django built-in auth with profile extension |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- pip

### Setup

```bash
# 1. Clone the repo
git clone https://github.com/Divya241181/Student-Feedback-System.git
cd Student-Feedback-System

# 2. Create virtual environment
python -m venv .venv
.venv\Scripts\activate       # Windows
# source .venv/bin/activate  # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Apply migrations
python manage.py migrate

# 5. Create a superuser (admin)
python manage.py createsuperuser

# 6. Run the dev server
python manage.py runserver
```

Then visit **http://127.0.0.1:8000/**

---

## 📁 Project Structure

```
Student-Feedback-System/
├── core/                   # Django project settings
│   ├── settings.py
│   └── urls.py
├── feedback/               # Main app
│   ├── models.py           # 9 models: Faculty, Student, Course, Survey, CO, Question…
│   ├── views.py            # All views (faculty + student + admin)
│   ├── forms.py            # ModelForms with styled widgets
│   ├── urls.py
│   ├── templates/
│   │   └── feedback/
│   │       ├── base.html           # Global layout, design system
│   │       ├── login.html          # Glassmorphism login
│   │       ├── faculty_dashboard.html
│   │       ├── student_dashboard.html
│   │       ├── survey_detail.html  # Survey builder (HTMX)
│   │       ├── take_survey.html    # Student survey form
│   │       ├── survey_results.html # Analytics & charts
│   │       └── partials/           # HTMX partials
│   └── static/
│       └── images/logo.png
├── sample_students.csv     # Sample import data
├── sample_faculty.csv
├── sample_courses.csv
├── requirements.txt
└── manage.py
```

---

## 📊 Data Models

```
FacultyProfile  ←──── User (Django built-in)
StudentProfile  ←──── User
Course          ←──── FacultyProfile, StudentProfile (M2M)
Survey          ←──── Course
CourseOutcome   ←──── Course
Question        ←──── Survey, CourseOutcome
MCQOption       ←──── Question
SurveyResponse  ←──── Survey, StudentProfile
Answer          ←──── SurveyResponse, Question
```

---

## 📥 Bulk Import (CSV Format)

**Students:** `first_name, last_name, username, password, enrollment_no, branch, semester, batch`

**Faculty:** `first_name, last_name, username, password, employee_id, department, designation`

**Courses:** `code, name, credits, semester, batch, faculty_employee_id`

> Import Faculty before Courses!

---

## 📄 License

MIT License — free to use and modify.

---

*Built with ❤️ by Divya Patel · KPGU*
