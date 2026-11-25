"""
Expose country and language reference data in Django Admin.
"""

from django.contrib import admin

from django_media_tracker.apps.locales.models import Country
from django_media_tracker.apps.locales.models import ExtendedLanguageSubtag
from django_media_tracker.apps.locales.models import Language
from django_media_tracker.apps.locales.models import LanguageExtension
from django_media_tracker.apps.locales.models import LanguageVariant
from django_media_tracker.apps.locales.models import PrimaryLanguageSubtag
from django_media_tracker.apps.locales.models import RegionSubtag
from django_media_tracker.apps.locales.models import ScriptSubtag
from django_media_tracker.apps.locales.models import VariantSubtag


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    """
    Browse countries by English name or any of their ISO codes.
    """

    list_display = (
        'name',
        'alpha2',
        'alpha3',
        'numeric_code',
    )
    search_fields = (
        'name',
        'name_full',
        '^alpha2',
        '^alpha3',
        '^numeric_code',
    )
    ordering = ('name',)


@admin.register(ScriptSubtag, VariantSubtag)
class SubtagAdmin(admin.ModelAdmin):
    """
    Browse script and variant subtags by code or name.
    """

    list_display = (
        'code',
        'name',
        'added_on',
        'deprecated_on',
    )
    search_fields = (
        '^code',
        'name',
    )
    ordering = ('code',)


@admin.register(PrimaryLanguageSubtag)
class PrimaryLanguageSubtagAdmin(SubtagAdmin):
    """
    Browse primary language subtags and edit their registry relationships.
    """

    list_filter = (
        'language_type',
        'scope',
    )
    autocomplete_fields = (
        'macrolanguage',
        'suppress_script',
    )


@admin.register(RegionSubtag)
class RegionSubtagAdmin(SubtagAdmin):
    """
    Browse region subtags and their associated countries.
    """

    autocomplete_fields = ('country',)


@admin.register(ExtendedLanguageSubtag)
class ExtendedLanguageSubtagAdmin(admin.ModelAdmin):
    """
    Browse extlangs and their required prefixes.
    """

    list_display = (
        'language',
        'prefix',
        'scope',
        'added_on',
    )
    list_select_related = (
        'language',
        'prefix',
    )
    autocomplete_fields = (
        'language',
        'prefix',
    )
    search_fields = (
        '^language__code',
        'language__name',
        '^prefix__code',
    )


class LanguageVariantInline(admin.TabularInline):
    """
    Edit the variants and their positions on a tag.
    """

    model = LanguageVariant
    extra = 0
    autocomplete_fields = ('variant',)
    ordering = ('position',)


class LanguageExtensionInline(admin.TabularInline):
    """
    Edit extension sequences on a tag.
    """

    model = LanguageExtension
    extra = 0


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    """
    Browse language tags and manage their component records.
    """

    list_display = (
        'primary_language',
        'extlang',
        'script',
        'region',
        'private_use',
        'added_on',
    )
    list_select_related = (
        'primary_language',
        'extlang__language',
        'script',
        'region',
    )
    search_fields = (
        '^primary_language__code',
        'primary_language__name',
        '^extlang__language__code',
        '^script__code',
        '^region__code',
        '^variants__code',
    )
    autocomplete_fields = (
        'primary_language',
        'extlang',
        'script',
        'region',
    )
    inlines = (
        LanguageVariantInline,
        LanguageExtensionInline,
    )


@admin.register(LanguageVariant)
class LanguageVariantAdmin(admin.ModelAdmin):
    """
    Manage variant assignments and their order directly.
    """

    list_display = (
        'variant',
        'position',
        'language_id',
    )
    list_select_related = ('variant',)
    autocomplete_fields = (
        'language',
        'variant',
    )
    search_fields = (
        '^variant__code',
        '^language__primary_language__code',
    )


@admin.register(LanguageExtension)
class LanguageExtensionAdmin(admin.ModelAdmin):
    """
    Manage extension assignments directly.
    """

    list_display = (
        'singleton',
        'value',
        'language_id',
    )
    autocomplete_fields = ('language',)
    search_fields = (
        '^singleton',
        'value',
        '^language__primary_language__code',
    )
