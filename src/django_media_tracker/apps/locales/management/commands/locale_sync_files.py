"""
Refresh the project's locale reference files.
"""

import csv
from argparse import ArgumentParser
from functools import cache
from http.client import HTTPException
from pathlib import Path
from tempfile import TemporaryDirectory

from django.core.management.base import BaseCommand
from django.core.management.base import CommandError

from django_media_tracker.apps.locales import sync_files
from django_media_tracker.apps.locales.sync_files import DATASETS


class Command(BaseCommand):
    """
    Save fresh copies of the locale reference datasets.
    """

    help = 'Download country, language, script, and IANA registry files.'
    requires_system_checks = []

    def add_arguments(self, parser: ArgumentParser) -> None:
        """
        Allow each destination to be overridden independently.
        """
        sync_files.add_path_arguments(parser, 'Output')

    def handle(self, *args: object, **options: str | Path) -> None:
        """
        Refresh each file independently and report any failures together.
        """
        paths = sync_files.dataset_paths(options)
        if len({path.resolve() for path in paths.values()}) != len(paths):
            raise CommandError('Each locale dataset must have a distinct output path.')

        fetch = cache(sync_files.download)
        failures: list[str] = []
        for name, _, load in DATASETS:
            destination = paths[name]
            try:
                contents = load(fetch)
                destination.parent.mkdir(parents=True, exist_ok=True)
                with TemporaryDirectory(dir=destination.parent) as directory:
                    staged = Path(directory) / destination.name
                    staged.write_bytes(contents)
                    staged.replace(destination)
            except (
                OSError,
                HTTPException,
                ValueError,
                KeyError,
                TypeError,
                csv.Error,
            ) as error:
                failures.append(f'{name}: {error}')
            else:
                self.stdout.write(f'Saved {name} to {destination}')
        if failures:
            raise CommandError('\n'.join(failures))
