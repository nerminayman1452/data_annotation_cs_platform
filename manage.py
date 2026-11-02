#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

q_cluster = None

def main():
    """Run administrative tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "base.settings.development")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    if sys.argv[1] == "runserver":
        execute_from_command_line([sys.argv[0], "migrate"])

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
