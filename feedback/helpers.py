"""
feedback/helpers.py
===================
Reusable role-detection utilities used across views and decorators.

We use `hasattr` because OneToOneField creates a reverse accessor on the
User model. If a FacultyProfile exists for that user, `user.faculty_profile`
is accessible — otherwise Django raises RelatedObjectDoesNotExist.
hasattr() catches that exception and returns False cleanly.
"""


def is_faculty(user):
    """Returns True if this User has a linked FacultyProfile."""
    return hasattr(user, 'faculty_profile')


def is_student(user):
    """Returns True if this User has a linked StudentProfile."""
    return hasattr(user, 'student_profile')


def get_user_role(user):
    """
    Returns 'faculty', 'student', or 'admin' string for the given user.
    Useful for template context and conditional logic.
    """
    if user.is_superuser or user.is_staff:
        return 'admin'
    if is_faculty(user):
        return 'faculty'
    if is_student(user):
        return 'student'
    return 'unknown'
