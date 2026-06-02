"""
feedback/management/commands/close_expired_surveys.py
=====================================================
Management command that finds all published surveys whose end_date has
passed and unpublishes them (sets is_published=False).

Why unpublish instead of a separate 'closed' status?
  Our Survey model uses a boolean is_published + date window to determine
  activity. Once end_date passes, is_active() already returns False, so
  surveys are naturally inactive. However, explicitly setting is_published=False
  on expired surveys gives a clean audit trail in admin and signals clearly
  that the survey collection period is done.

Usage:
  python manage.py close_expired_surveys

Schedule with cron (Linux/Mac):
  # crontab -e
  0 0 * * * /path/to/venv/bin/python /path/to/manage.py close_expired_surveys

Schedule with Windows Task Scheduler:
  Program: C:\\path\\to\\venv\\Scripts\\python.exe
  Arguments: C:\\path\\to\\manage.py close_expired_surveys
  Trigger: Daily at 00:00
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from feedback.models import Survey


class Command(BaseCommand):
    help = 'Unpublishes all surveys whose end_date has passed'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show which surveys would be closed without actually closing them.',
        )

    def handle(self, *args, **options):
        now     = timezone.now()
        dry_run = options['dry_run']

        # Find published surveys that are past their end_date
        expired = Survey.objects.filter(
            is_published=True,
            end_date__lt=now,
        ).select_related('course')

        count = expired.count()

        if count == 0:
            self.stdout.write(self.style.SUCCESS('No expired surveys found. All good!'))
            return

        # List what would be / was closed
        for survey in expired:
            self.stdout.write(
                f'  {"[DRY RUN] " if dry_run else ""}Closing: '
                f'"{survey.title}" (course: {survey.course.code}, '
                f'ended: {survey.end_date.strftime("%d %b %Y %H:%M")})'
            )

        if not dry_run:
            expired.update(is_published=False)
            self.stdout.write(
                self.style.SUCCESS(f'\nSuccessfully closed {count} expired survey(s).')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'\n[DRY RUN] Would close {count} survey(s). '
                                   f'Run without --dry-run to apply.')
            )
