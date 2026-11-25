"""
Test loading saved locale reference files into the database.
"""

import json
from datetime import date
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from django_media_tracker.apps.locales.models import Country
from django_media_tracker.apps.locales.models import ExtendedLanguageSubtag
from django_media_tracker.apps.locales.models import Language
from django_media_tracker.apps.locales.models import LanguageScope
from django_media_tracker.apps.locales.models import PrimaryLanguageSubtag
from django_media_tracker.apps.locales.models import RegionSubtag
from django_media_tracker.apps.locales.models import ScriptSubtag


class LocaleSyncDatabaseTests(TestCase):
    """
    Verify file overrides, relationships, repeat imports, and rollback.
    """

    def setUp(self) -> None:
        """
        Write a minimal set of synced reference files.
        """
        root = Path(self.enterContext(TemporaryDirectory()))
        self.enterContext(self.settings(BASE_DIR=root / 'src'))
        self.data = root / 'etc'
        self.data.mkdir()
        self.iana = root / 'registry.txt'
        self.iana.write_text(
            'File-Date: 2026-11-18\n'
            '%%\nType: language\nSubtag: en\nDescription: English\n'
            'Suppress-Script: Latn\nAdded: 2005-10-16\n'
            '%%\nType: language\nSubtag: zh\nDescription: Chinese\n'
            'Scope: macrolanguage\n'
            '%%\nType: language\nSubtag: yue\nDescription: Cantonese\n'
            'Macrolanguage: zh\n'
            '%%\nType: language\nSubtag: cel\nDescription: Celtic\nScope: collection\n'
            '%%\nType: language\nSubtag: iw\nDescription: Hebrew\n'
            'Deprecated: 1989-01-01\n'
            '%%\nType: extlang\nSubtag: yue\nDescription: Cantonese\nPrefix: zh\n'
            'Added: 2009-07-29\n'
            '%%\nType: region\nSubtag: US\nDescription: United States\n'
            'Added: 2005-10-16\n'
            '%%\nType: region\nSubtag: 001\nDescription: World\n'
            '%%\nType: script\nSubtag: Latn\nDescription: Latin\nAdded: 2005-10-16\n'
            '%%\nType: variant\nSubtag: boont\nDescription: Boontling\n'
            'Added: 2006-09-18\n'
            '%%\nType: redundant\nTag: en-boont\nDescription: Boontling\n'
            'Added: 2003-02-14\n',
            encoding='utf-8',
        )
        self.write_rows(
            'country_iso-3166-1.json',
            'countries',
            [
                {
                    'alpha2_code': 'US',
                    'alpha3_code': 'USA',
                    'numeric_code': '840',
                    'short_name': 'UNITED STATES',
                    'short_name_lower_case': 'United States',
                    'full_name': 'United States of America',
                },
            ],
        )
        self.write_rows(
            'country_un-m-49.json',
            'countries',
            [
                {
                    'm49_code': '840',
                    'country_or_area': 'United States of America',
                    'global_code': '001',
                    'global_name': 'World from M49',
                    'region_code': '',
                    'region_name': '',
                    'subregion_code': '',
                    'subregion_name': '',
                    'intermediate_region_code': '',
                    'intermediate_region_name': '',
                },
            ],
        )
        self.write_rows(
            'language_iso-639-1.json',
            'languages',
            [
                {
                    'alpha2': 'en',
                    'name_en': 'English from Set 1',
                },
            ],
        )
        self.write_rows(
            'language_iso-639-2.json',
            'languages',
            [
                {
                    'alpha3_terminological': 'eng',
                    'name_en': 'English',
                },
            ],
        )
        self.write_rows(
            'language_iso-639-3.json',
            'languages',
            [
                {
                    'id': 'eng',
                    'part1': 'en',
                    'ref_name': 'English',
                    'language_type': 'L',
                },
            ],
        )
        self.write_rows(
            'language_iso-639-5.json',
            'languages',
            [
                {
                    'alpha3': 'cel',
                    'name_en': 'Celtic languages',
                },
            ],
        )
        self.write_rows(
            'scripts_iso-15924.json',
            'scripts',
            [
                {
                    'code': 'Latn',
                    'name_en': 'Latin from ISO 15924',
                },
            ],
        )

    def write_rows(
        self, filename: str, key: str, records: list[dict[str, str]]
    ) -> None:
        """
        Write one input dataset using the downloader's JSON structure.
        """
        payload = {
            key: records,
        }
        (self.data / filename).write_text(json.dumps(payload), encoding='utf-8')

    def test_sync_database_twice(self) -> None:
        """
        Import linked records and preserve IDs on repeated runs.
        """
        call_command('locale_sync_db', '--iana-path', str(self.iana), stdout=StringIO())
        country = Country.objects.get(alpha2='US')
        self.assertEqual(RegionSubtag.objects.get(code='US').country, country)
        self.assertEqual(RegionSubtag.objects.get(code='001').name, 'World from M49')
        self.assertIsNone(RegionSubtag.objects.get(code='001').country)
        english = PrimaryLanguageSubtag.objects.get(code='en')
        self.assertEqual(english.scope, LanguageScope.INDIVIDUAL)
        self.assertEqual(english.name, 'English from Set 1')
        self.assertEqual(
            english.language_type, PrimaryLanguageSubtag.LanguageType.LIVING
        )
        self.assertEqual(english.suppress_script, ScriptSubtag.objects.get(code='Latn'))
        self.assertEqual(english.suppress_script.name, 'Latin from ISO 15924')
        self.assertEqual(
            PrimaryLanguageSubtag.objects.get(code='cel').name, 'Celtic languages'
        )
        extended = ExtendedLanguageSubtag.objects.get(language__code='yue')
        self.assertEqual(extended.scope, LanguageScope.INDIVIDUAL)
        self.assertEqual(extended.prefix.scope, LanguageScope.MACROLANGUAGE)
        self.assertEqual(
            PrimaryLanguageSubtag.objects.get(code='cel').scope,
            LanguageScope.COLLECTION,
        )
        self.assertEqual(extended.prefix.code, 'zh')
        self.assertEqual(extended.language.macrolanguage, extended.prefix)
        self.assertFalse(Language.objects.filter(primary_language__code='iw').exists())
        self.assertIn('en-boont', {language.tag for language in Language.objects.all()})
        tags_before = set(Language.objects.values_list('pk', flat=True))

        call_command('locale_sync_db', iana_path=self.iana, stdout=StringIO())

        self.assertEqual(Country.objects.get(alpha2='US').pk, country.pk)
        self.assertEqual(
            set(Language.objects.values_list('pk', flat=True)), tags_before
        )

    def test_invalid_input_rolls_back_changes(self) -> None:
        """
        Keep the transaction from partially updating the reference tables.
        """
        path = self.data / 'language_iso-639-3.json'
        path.write_text('invalid JSON', encoding='utf-8')

        with self.assertRaisesMessage(CommandError, path.name):
            call_command('locale_sync_db', iana_path=self.iana, stdout=StringIO())

        self.assertFalse(Country.objects.exists())
        self.assertFalse(RegionSubtag.objects.exists())

    def test_registration_dates_are_imported_and_refreshed(self) -> None:
        """
        Store the dates for each record and backfill an existing whole tag.
        """
        call_command('locale_sync_db', iana_path=self.iana, stdout=StringIO())
        english = PrimaryLanguageSubtag.objects.get(code='en')
        self.assertEqual(english.added_on, date(2005, 10, 16))
        self.assertEqual(english.suppress_script.added_on, date(2005, 10, 16))
        self.assertEqual(
            RegionSubtag.objects.get(code='US').added_on, date(2005, 10, 16)
        )
        self.assertEqual(
            ExtendedLanguageSubtag.objects.get(language__code='yue').added_on,
            date(2009, 7, 29),
        )
        bare_tag = Language.objects.get(primary_language=english, variants__isnull=True)
        self.assertIsNone(bare_tag.added_on)
        tag = Language.objects.get(primary_language=english, variants__code='boont')
        self.assertEqual(tag.variants.get().added_on, date(2006, 9, 18))
        self.assertEqual(tag.added_on, date(2003, 2, 14))
        Language.objects.filter(pk=tag.pk).update(added_on=None)

        call_command('locale_sync_db', iana_path=self.iana, stdout=StringIO())
        tag.refresh_from_db()

        self.assertEqual(tag.added_on, date(2003, 2, 14))

    def test_extlang_scope_is_refreshed_from_its_own_record(self) -> None:
        """
        Store an explicit extlang scope and reset it to individual when omitted.
        """
        registry = self.iana.read_text(encoding='utf-8')
        self.iana.write_text(
            registry.replace('Prefix: zh\n', 'Prefix: zh\nScope: macrolanguage\n'),
            encoding='utf-8',
        )
        call_command('locale_sync_db', iana_path=self.iana, stdout=StringIO())
        extlang = ExtendedLanguageSubtag.objects.get(language__code='yue')
        self.assertEqual(extlang.scope, LanguageScope.MACROLANGUAGE)
        self.assertEqual(extlang.language.scope, LanguageScope.INDIVIDUAL)

        self.iana.write_text(registry, encoding='utf-8')
        call_command('locale_sync_db', iana_path=self.iana, stdout=StringIO())
        extlang.refresh_from_db()

        self.assertEqual(extlang.scope, LanguageScope.INDIVIDUAL)

    def test_unknown_scope_rejects_import(self) -> None:
        """
        Reject an unknown registry scope without partially loading the database.
        """
        registry = self.iana.read_text(encoding='utf-8')
        self.iana.write_text(
            registry.replace('Scope: collection', 'Scope: unknown'),
            encoding='utf-8',
        )
        with self.assertRaisesMessage(CommandError, 'unknown'):
            call_command('locale_sync_db', iana_path=self.iana, stdout=StringIO())

        self.assertFalse(PrimaryLanguageSubtag.objects.exists())
        self.assertFalse(Country.objects.exists())
