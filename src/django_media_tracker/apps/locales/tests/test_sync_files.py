"""
Test locale reference sync without network access.
"""

import json
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from urllib.error import URLError

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase

from django_media_tracker.apps.locales import sync_files
from django_media_tracker.apps.locales.management.commands.locale_sync_files import (
    DATASETS,
)


class LocaleSyncFilesTests(SimpleTestCase):
    """
    Exercise source conversion, destination handling, and failed downloads.
    """

    def setUp(self) -> None:
        """
        Set up a temporary project root and representative publisher responses.
        """
        self.root = Path(self.enterContext(TemporaryDirectory()))
        self.output = self.root / 'etc'
        self.enterContext(self.settings(BASE_DIR=self.root / 'src'))
        world = '<td>001</td><td>World</td>' + '<td></td>' * 6
        self.registry = (
            b'File-Date: 2026-11-18\n%%\nType: language\nSubtag: zh\n'
            b'Scope: macrolanguage\n'
        )
        self.sources = {
            sync_files.ISO_COUNTRY_ASSIGNMENTS_URL: (
                b'{"3166-1":[{"alpha_2":"AU","alpha_3":"AUS","numeric":"036"}]}'
            ),
            sync_files.ISO_COUNTRY_DETAILS_URL: (
                b'{"countries":[{"alpha2_code":"AU","alpha3_code":"AUS",'
                b'"numeric_code":36,"status":"Officially assigned","subdivisions":[]}]}'
            ),
            f'{sync_files.ISO_COUNTRY_NAMES_URL}-EN.csv': b'Alpha-2,Alpha-3\nAU,AUS\n',
            f'{sync_files.ISO_COUNTRY_NAMES_URL}-FR.csv': (
                'Alpha-2,Alpha-3,Code numérique,Nom court,Nom court minuscule,'
                'Nom complet,Remarques\nAU,AUS,036,Australie,australie,,\n'
            ).encode(),
            sync_files.M49_URL: (
                '<table id="downloadTableEN"><tr><td>Header</td></tr><tr>'
                f'{world}<td>Australia</td><td>036</td><td>AU</td><td>AUS</td>'
                '<td></td><td></td><td></td></tr></table>'
            ).encode(),
            sync_files.ISO_639_2_URL: b'eng||en|English|anglais\nace|||Achinese|aceh\n',
            sync_files.ISO_639_3_URL: b'Id\tScope\tRef_Name\neng\tI\tEnglish\n',
            sync_files.ISO_639_5_URL: (
                b'<table class="Dynamic639-5OutputTables"><tr><th>Header</th></tr>'
                b'<tr><td>gem</td><td>Germanic languages</td><td>germaniques</td>'
                b'<td></td><td>ine : gem</td><td>Note</td></tr>'
                b'<tr><td colspan="6"><ol><li id="note-a">Note text</li></ol></td></tr>'
                b'</table>'
            ),
            sync_files.ISO_15924_URL: (
                b'# header\nLatn;215;Latin;latin;Latin;1.1;2004-05-01\n'
            ),
            sync_files.IANA_URL: self.registry,
        }

    def test_saves_all_datasets_and_honors_path_override(self) -> None:
        """
        Save every dataset and retain numeric, bilingual, and nested attributes.
        """
        iana_path = self.root / 'custom' / 'registry.txt'
        with patch.object(
            sync_files, 'download', side_effect=self.sources.__getitem__
        ) as fetch:
            call_command('locale_sync_files', iana_path=iana_path, stdout=StringIO())

        self.assertEqual(iana_path.read_bytes(), self.registry)
        self.assertFalse((self.output / 'language_iana-subtag-registry.txt').exists())
        for _, filename, _ in DATASETS[:-1]:
            self.assertTrue((self.output / filename).is_file())
        country = self.read_json('country_iso-3166-1.json')['countries'][0]
        self.assertEqual(country['numeric_code'], '036')
        self.assertEqual(country['short_name_fr'], 'Australie')
        self.assertEqual(country['subdivisions'], [])
        m49 = self.read_json('country_un-m-49.json')['countries'][0]
        self.assertEqual(m49['m49_code'], '036')
        self.assertEqual(len(m49), 15)
        self.assertEqual(len(self.read_json('language_iso-639-1.json')['languages']), 1)
        self.assertEqual(len(self.read_json('language_iso-639-2.json')['languages']), 2)
        self.assertEqual(
            self.read_json('language_iso-639-3.json')['languages'][0]['scope'], 'I'
        )
        self.assertEqual(
            self.read_json('language_iso-639-5.json')['languages'][0]['notes'], 'Note'
        )
        self.assertEqual(
            self.read_json('language_iso-639-5.json')['notes'],
            {
                'note-a': 'Note text',
            },
        )
        self.assertEqual(
            self.read_json('scripts_iso-15924.json')['scripts'][0]['numeric'], '215'
        )
        self.assertEqual(fetch.call_count, len(self.sources))

    def test_failed_download_preserves_file_and_other_datasets_still_save(self) -> None:
        """
        Leave existing files untouched on failure and report the failed dataset.
        """
        self.output.mkdir()
        destination = self.output / 'country_un-m-49.json'
        destination.write_bytes(b'previous data')

        def fetch(url: str) -> bytes:
            if url == sync_files.M49_URL:
                raise URLError('offline')
            return self.sources[url]

        with (
            patch.object(sync_files, 'download', side_effect=fetch),
            self.assertRaisesMessage(CommandError, 'un-m-49'),
        ):
            call_command('locale_sync_files', stdout=StringIO())
        self.assertEqual(destination.read_bytes(), b'previous data')
        self.assertEqual(
            (self.output / 'language_iana-subtag-registry.txt').read_bytes(),
            self.registry,
        )

    def read_json(self, filename: str) -> dict[str, list[dict[str, object]]]:
        """
        Read a generated dataset from its default path.
        """
        return json.loads((self.output / filename).read_text(encoding='utf-8'))
