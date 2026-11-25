"""
Refresh the project's locale reference files.
"""

import csv
from argparse import ArgumentParser
from functools import cache
from functools import partial
from http.client import HTTPException
from pathlib import Path
from tempfile import TemporaryDirectory

from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.management.base import CommandError

from django_media_tracker.apps.locales import sync_files

DATASETS = (
    (
        'iso-3166-1',
        'country_iso-3166-1.json',
        sync_files.load_iso_countries,
    ),
    (
        'un-m-49',
        'country_un-m-49.json',
        sync_files.load_m49_countries,
    ),
    (
        'iso-639-1',
        'language_iso-639-1.json',
        partial(sync_files.load_iso_languages, alpha2_only=True),
    ),
    (
        'iso-639-2',
        'language_iso-639-2.json',
        sync_files.load_iso_languages,
    ),
    (
        'iso-639-3',
        'language_iso-639-3.json',
        sync_files.load_iso_639_3,
    ),
    (
        'iso-639-5',
        'language_iso-639-5.json',
        sync_files.load_iso_639_5,
    ),
    (
        'iso-15924',
        'scripts_iso-15924.json',
        sync_files.load_iso_scripts,
    ),
    (
        'iana',
        'language_iana-subtag-registry.txt',
        sync_files.load_iana_registry,
    ),
)


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
        for name, filename, _ in DATASETS:
            parser.add_argument(
                f'--{name}-path',
                dest=name.replace('-', '_'),
                type=Path,
                default=settings.BASE_DIR.parent / 'etc' / filename,
                help=f'Output path (default: etc/{filename}).',
            )

    def handle(self, *args: object, **options: str | Path) -> None:
        """
        Refresh each file independently and report any failures together.
        """
        paths = {name: Path(options[name.replace('-', '_')]) for name, _, _ in DATASETS}
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
