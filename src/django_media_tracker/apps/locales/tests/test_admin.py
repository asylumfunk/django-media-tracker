"""
Verify Django Admin access to locale reference models.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from django_media_tracker.apps.locales.models import Country
from django_media_tracker.apps.locales.models import Language
from django_media_tracker.apps.locales.models import LanguageExtension
from django_media_tracker.apps.locales.models import LanguageVariant
from django_media_tracker.apps.locales.models import PrimaryLanguageSubtag
from django_media_tracker.apps.locales.models import VariantSubtag


class LocaleAdminTests(TestCase):
    """
    Exercise the locale admin pages through Django's HTTP client.
    """

    @classmethod
    def setUpTestData(cls) -> None:
        """
        Create an administrator and a language tag with editable components.
        """
        cls.administrator = get_user_model().objects.create_superuser(
            username='locale-admin',
        )
        primary = PrimaryLanguageSubtag.objects.create(code='en', name='English')
        cls.language = Language.objects.create(primary_language=primary)
        variant = VariantSubtag.objects.create(code='boont', name='Boontling')
        LanguageVariant.objects.create(
            language=cls.language, variant=variant, position=0
        )
        LanguageExtension.objects.create(
            language=cls.language, singleton='u', value='ca-gregory'
        )

    def test_all_locale_models_have_admin_pages(self) -> None:
        """
        Open the app index and changelist for each concrete model.
        """
        self.client.force_login(self.administrator)
        self.assertEqual(self.client.get('/admin/locales/').status_code, 200)
        for name in (
            'country',
            'extendedlanguagesubtag',
            'language',
            'languageextension',
            'languagevariant',
            'primarylanguagesubtag',
            'regionsubtag',
            'scriptsubtag',
            'variantsubtag',
        ):
            with self.subTest(model=name):
                index = reverse(f'admin:locales_{name}_changelist')
                self.assertEqual(self.client.get(index).status_code, 200)

    def test_language_change_form_includes_related_records(self) -> None:
        """
        Show editable variants and extensions on the language tag form.
        """
        self.client.force_login(self.administrator)
        url = reverse(
            'admin:locales_language_change',
            args=[
                self.language.pk,
            ],
        )
        response = self.client.get(url)

        self.assertContains(response, 'variant_links-0-position')
        self.assertContains(response, 'extensions-0-value')
        self.assertContains(response, 'ca-gregory')

    def test_admin_can_add_country(self) -> None:
        """
        Save a country through the standard Django Admin add form.
        """
        self.client.force_login(self.administrator)
        response = self.client.post(
            reverse('admin:locales_country_add'),
            {
                'name': 'Australia',
                'alpha2': 'AU',
                'alpha3': 'AUS',
                'numeric_code': '036',
            },
        )

        self.assertRedirects(response, reverse('admin:locales_country_changelist'))
        self.assertEqual(Country.objects.get(alpha2='AU').numeric_code, '036')

    def test_staff_without_model_permission_cannot_view_country_list(self) -> None:
        """
        Apply Django's model-level permissions to the country changelist.
        """
        staff = get_user_model().objects.create_user(
            username='locale-staff', is_staff=True
        )
        self.client.force_login(staff)

        response = self.client.get(reverse('admin:locales_country_changelist'))

        self.assertEqual(response.status_code, 403)
