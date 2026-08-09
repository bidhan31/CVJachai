#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""

import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    # AUTO-MIGRATE ON STARTUP (For Hugging Face / Production)
    if any(arg in sys.argv for arg in ['runserver', 'gunicorn']) or os.getenv('K_SERVICE'):
        try:
            print("Auto-running migrations...")
            execute_from_command_line(['manage.py', 'migrate', '--noinput'])
        except Exception as e:
            print(f"Migration error: {e}")

    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
