import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

try:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

    # Auto-run migrate and collectstatic on every app startup/restart.
    # This means you never need to run these manually from a terminal.
    import django
    django.setup()

    from django.core.management import call_command
    call_command('migrate', '--noinput', verbosity=0)
    call_command('collectstatic', '--noinput', verbosity=0)

    from django.core.wsgi import get_wsgi_application
    application = get_wsgi_application()

except Exception as e:
    import traceback
    with open(os.path.join(os.path.dirname(__file__), 'wsgi_error.log'), 'w') as f:
        f.write(traceback.format_exc())
    raise e
