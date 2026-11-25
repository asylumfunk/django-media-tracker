"""
Test locale reference models and BCP 47 tag composition.
"""

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db import transaction
from django.test import TestCase

from django_media_tracker.apps.locales.models import Country
from django_media_tracker.apps.locales.models import ExtendedLanguageSubtag
from django_media_tracker.apps.locales.models import Language
from django_media_tracker.apps.locales.models import LanguageExtension
from django_media_tracker.apps.locales.models import LanguageVariant
from django_media_tracker.apps.locales.models import PrimaryLanguageSubtag
from django_media_tracker.apps.locales.models import RegionSubtag
from django_media_tracker.apps.locales.models import ScriptSubtag
from django_media_tracker.apps.locales.models import VariantSubtag


class LocaleModelTests(TestCase):
    """
    Verify country codes, subtag relationships, and tag constraints.
    """

    def test_country_codes_and_region_association(self) -> None:
        """
        Retain leading zeros and associate a region with its matching country.
        """
        country = Country(
            name='Australia',
            alpha2='AU',
            alpha3='AUS',
            numeric_code='036',
        )
        country.full_clean()
        country.save()
        country.refresh_from_db()
        self.assertEqual(country.numeric_code, '036')
        self.assertEqual(str(country), 'Australia')

        region = RegionSubtag(name='Australia', code='AU', country=country)
        region.full_clean()
        region.code = '419'
        with self.assertRaisesMessage(ValidationError, 'does not match'):
            region.full_clean()

    def test_numeric_region_without_country(self) -> None:
        """
        Render a tag with a UN M49 region that spans multiple countries.
        """
        spanish = PrimaryLanguageSubtag.objects.create(
            name='Spanish',
            code='es',
            language_type=PrimaryLanguageSubtag.LanguageType.LIVING,
        )
        region = RegionSubtag.objects.create(
            name='Latin America and the Caribbean', code='419'
        )
        self.assertEqual(
            str(Language(primary_language=spanish, region=region)), 'es-419'
        )

    def test_extlang_requires_its_registered_prefix(self) -> None:
        """
        Accept Cantonese with its registered prefix and reject a different one.
        """
        chinese = PrimaryLanguageSubtag.objects.create(name='Chinese', code='zh')
        cantonese = PrimaryLanguageSubtag.objects.create(name='Cantonese', code='yue')
        english = PrimaryLanguageSubtag.objects.create(name='English', code='en')
        extlang = ExtendedLanguageSubtag(language=cantonese, prefix=chinese)
        extlang.full_clean()
        extlang.save()

        tag = Language(primary_language=chinese, extlang=extlang)
        tag.full_clean()
        self.assertEqual(tag.tag, 'zh-yue')
        tag.primary_language = english
        with self.assertRaisesMessage(ValidationError, 'requires a different prefix'):
            tag.full_clean()

        extlang.language = english
        with self.assertRaisesMessage(ValidationError, 'three-letter code'):
            extlang.full_clean()

    def test_tag_uses_ordered_variants_and_extensions(self) -> None:
        """
        Render variant positions, sorted extensions, and the final private-use suffix.
        """
        slovenian = PrimaryLanguageSubtag.objects.create(name='Slovenian', code='sl')
        script = ScriptSubtag.objects.create(name='Latin', code='Latn')
        language = Language.objects.create(
            primary_language=slovenian, script=script, private_use='catalog'
        )
        resian = VariantSubtag.objects.create(name='Resian', code='rozaj')
        biske = VariantSubtag.objects.create(name='San Giorgio dialect', code='biske')
        LanguageVariant.objects.create(language=language, variant=biske, position=1)
        LanguageVariant.objects.create(language=language, variant=resian, position=0)
        LanguageExtension.objects.create(
            language=language, singleton='u', value='ca-gregory'
        )
        LanguageExtension.objects.create(language=language, singleton='t', value='en')

        self.assertEqual(
            language.tag, 'sl-Latn-rozaj-biske-t-en-u-ca-gregory-x-catalog'
        )

        with self.assertRaises(IntegrityError), transaction.atomic():
            LanguageVariant.objects.create(
                language=language, variant=resian, position=2
            )
        with self.assertRaises(IntegrityError), transaction.atomic():
            LanguageExtension.objects.create(
                language=language, singleton='u', value='nu-latn'
            )
