# KSTAR Feedback System — Setup Guide

## One-time setup (run these once)

```powershell
# 1. Open this folder in PowerShell / Terminal

# 2. Create virtual environment
python -m venv .venv

# 3. Activate it
.venv\Scripts\activate

# 4. Install packages
pip install -r requirements.txt

# 5. Create database tables
python manage.py migrate

# 6. Create your admin login
python manage.py createsuperuser

# 7. Start the server
python manage.py runserver
```

## Every time after that

```powershell
.venv\Scripts\activate
python manage.py runserver
```

## Open in browser
http://127.0.0.1:8000/
