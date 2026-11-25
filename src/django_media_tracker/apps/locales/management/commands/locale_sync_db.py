"""
Populate the locale reference tables from local files.
"""

from argparse import ArgumentParser
from pathlib import Path

from django.core.management.base import BaseCommand
from django.core.management.base import CommandError
from django.db import DatabaseError

from django_media_tracker.apps.locales.sync_db import sync_database
from django_media_tracker.apps.locales.sync_files import add_path_arguments
from django_media_tracker.apps.locales.sync_files import dataset_paths


class Command(BaseCommand):
    """
    Import country and language reference data into the configured database.
    """

    help = 'Populate locale tables from the files downloaded by locale_sync_files.'

    def add_arguments(self, parser: ArgumentParser) -> None:
        """
        Expose the same file paths as the download command.
        """
        add_path_arguments(parser, 'Input')

    def handle(self, *args: object, **options: str | Path) -> None:
        """
        Run the import and report errors after rolling back the transaction.
        """
        try:
            sync_database(dataset_paths(options))
        except (OSError, ValueError, KeyError, TypeError, DatabaseError) as error:
            raise CommandError(f'Locale import failed: {error}') from error
        self.stdout.write(self.style.SUCCESS('Locale database synchronized.'))
