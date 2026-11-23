#!/usr/bin/env python
"""Run Django management commands."""

import os
import sys

from django.core.management import execute_from_command_line


def main() -> None:
    """Run a management command with the project settings."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_media_tracker.settings')
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
