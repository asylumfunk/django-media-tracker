"""
Populate locale reference tables from downloaded datasets.
"""

import json
import re
from datetime import date
from pathlib import Path
from typing import TypeVar

from django.db import models
from django.db import transaction

from django_media_tracker.apps.locales.models import Country
from django_media_tracker.apps.locales.models import ExtendedLanguageSubtag
from django_media_tracker.apps.locales.models import Language
from django_media_tracker.apps.locales.models import LanguageScope
from django_media_tracker.apps.locales.models import LanguageVariant
from django_media_tracker.apps.locales.models import PrimaryLanguageSubtag
from django_media_tracker.apps.locales.models import RegionSubtag
from django_media_tracker.apps.locales.models import ScriptSubtag
from django_media_tracker.apps.locales.models import VariantSubtag

RegistryRecord = dict[str, list[str]]
Registry = dict[str, dict[str, RegistryRecord]]
LocaleModel = TypeVar('LocaleModel', bound=models.Model)


def read_rows(path: Path, key: str) -> list[dict[str, str | None]]:
    """
    Read record objects from one downloaded JSON dataset.
    """
    try:
        records = json.loads(path.read_text(encoding='utf-8'))[key]
        if not isinstance(records, list) or any(
            not isinstance(row, dict) for row in records
        ):
            raise ValueError(f'Expected a list of {key}.')
    except (ValueError, KeyError, TypeError) as error:
        raise ValueError(f'{path}: {error}') from error
    return records


def read_registry(path: Path) -> Registry:
    """
    Read IANA records, including repeated and folded fields.
    """
    text = path.read_text(encoding='utf-8')
    header, separator, data = text.partition('\n%%\n')
    if not separator or not re.fullmatch(
        r'File-Date: [0-9]{4}-[0-9]{2}-[0-9]{2}', header
    ):
        raise ValueError(f'{path}: invalid IANA registry header.')

    registry: Registry = {}
    for block in re.split(r'^%%$', data, flags=re.MULTILINE):
        fields: RegistryRecord = {}
        field = ''
        for line in block.splitlines():
            if not line.strip():
                continue
            if line[0].isspace() and field:
                fields[field][-1] = f'{fields[field][-1]} {line.strip()}'
                continue
            field, colon, value = line.partition(':')
            if not colon or not field:
                raise ValueError(f'{path}: invalid registry field {line!r}.')
            fields.setdefault(field, []).append(value.strip())
        if fields:
            kind = registry_value(fields, 'Type')
            code = registry_value(fields, 'Subtag') or registry_value(fields, 'Tag')
            if not kind or not code or not registry_value(fields, 'Description'):
                raise ValueError(f'{path}: registry record is missing required fields.')
            if '..' in code:
                # A private-use range is not an individual registry entry.
                continue
            entries = registry.setdefault(kind, {})
            if code in entries:
                raise ValueError(f'{path}: duplicate {kind} registry record {code}.')
            entries[code] = fields
    if not registry.get('language'):
        raise ValueError(f'{path}: no primary language records.')
    return registry


def registry_value(fields: RegistryRecord, field: str) -> str:
    """
    Return the first value of an IANA field, or an empty string.
    """
    values = fields.get(field)
    return values[0] if values else ''


def language_scope(fields: RegistryRecord) -> LanguageScope:
    """
    Use individual scope when IANA omits the field and reject unknown values.
    """
    value = registry_value(fields, 'Scope')
    return LanguageScope(value) if value else LanguageScope.INDIVIDUAL


def deprecation_date(fields: RegistryRecord) -> date | None:
    """
    Convert an IANA deprecation date when one is present.
    """
    value = registry_value(fields, 'Deprecated')
    return date.fromisoformat(value) if value else None


def upsert(
    model: type[LocaleModel],
    rows: list[LocaleModel],
    key: str,
    *fields: str,
) -> dict[str, LocaleModel]:
    """
    Refresh records by their stable source keys and return their saved instances.
    """
    keys = [getattr(row, key) for row in rows]
    if len(keys) != len(set(keys)):
        raise ValueError(f'Duplicate keys for {model.__name__}.')
    model.objects.bulk_create(
        rows,
        update_conflicts=True,
        update_fields=fields,
        unique_fields=[
            key,
        ],
    )
    return model.objects.in_bulk(keys, field_name=key)


def m49_names(rows: list[dict[str, str | None]]) -> dict[str, str]:
    """
    Index country and geographic area names by their numeric M49 codes.
    """
    names = {}
    for row in rows:
        names[row['m49_code']] = row['country_or_area']
        for level in (
            'global',
            'region',
            'subregion',
            'intermediate_region',
        ):
            code = row[f'{level}_code']
            name = row[f'{level}_name']
            if code and name:
                names[code] = name
    return names


def sync_primary_languages(
    registry: dict[str, RegistryRecord],
    paths: dict[str, Path],
    scripts: dict[str, ScriptSubtag],
) -> dict[str, PrimaryLanguageSubtag]:
    """
    Enrich primary subtags with ISO names, living status, and IANA relationships.
    """
    names: dict[str, str] = {}
    language_types: dict[str, str] = {}
    for row in read_rows(paths['iso-639-3'], 'languages'):
        if row['ref_name']:
            names[row['id']] = row['ref_name']
        if row['language_type']:
            language_types[row['id']] = row['language_type']
            if row['part1']:
                language_types[row['part1']] = row['language_type']

    for row in read_rows(paths['iso-639-2'], 'languages'):
        names[row['alpha3_terminological']] = row['name_en'].split(';', 1)[0]
    for row in read_rows(paths['iso-639-5'], 'languages'):
        names[row['alpha3']] = row['name_en']
    for row in read_rows(paths['iso-639-1'], 'languages'):
        names[row['alpha2']] = row['name_en'].split(';', 1)[0]

    languages = upsert(
        PrimaryLanguageSubtag,
        [
            PrimaryLanguageSubtag(
                code=code,
                name=names.get(code) or registry_value(record, 'Description'),
                language_type=language_types.get(code, ''),
                scope=language_scope(record),
                deprecated_on=deprecation_date(record),
                suppress_script=scripts.get(registry_value(record, 'Suppress-Script')),
            )
            for code, record in registry.items()
        ],
        'code',
        'name',
        'language_type',
        'scope',
        'deprecated_on',
        'suppress_script',
    )
    for code, language in languages.items():
        language.macrolanguage = languages.get(
            registry_value(registry[code], 'Macrolanguage')
        )
    PrimaryLanguageSubtag.objects.bulk_update(
        languages.values(),
        [
            'macrolanguage',
        ],
    )
    return languages


def sync_language_tags(
    registry: Registry,
    primary: dict[str, PrimaryLanguageSubtag],
    extlangs: dict[int, ExtendedLanguageSubtag],
    scripts: dict[str, ScriptSubtag],
    regions: dict[str, RegionSubtag],
    variants: dict[str, VariantSubtag],
) -> None:
    """
    Seed active standalone languages and active, structured IANA whole tags.
    """
    bare_tags = Language.objects.filter(
        extlang__isnull=True,
        script__isnull=True,
        region__isnull=True,
        private_use='',
        variant_links__isnull=True,
        extensions__isnull=True,
    ).values_list('primary_language_id', flat=True)
    existing_primary = set(bare_tags)
    Language.objects.bulk_create(
        [
            Language(primary_language=language)
            for language in primary.values()
            if not language.deprecated_on and language.pk not in existing_primary
        ],
    )

    for tag, record in registry.get('redundant', {}).items():
        if registry_value(record, 'Deprecated'):
            continue
        code, *parts = tag.split('-')
        language = primary[code]
        extended = (
            extlangs.get(primary[parts[0]].pk)
            if parts and parts[0] in primary
            else None
        )
        if extended and extended.prefix_id == language.pk:
            parts.pop(0)
        else:
            extended = None
        script = scripts[parts.pop(0)] if parts and parts[0] in scripts else None
        region = regions[parts.pop(0)] if parts and parts[0] in regions else None
        variant_ids = [variants[part].pk for part in parts]
        matches = Language.objects.filter(
            primary_language=language,
            extlang=extended,
            script=script,
            region=region,
            private_use='',
            extensions__isnull=True,
        ).prefetch_related(
            models.Prefetch(
                'variant_links',
                queryset=LanguageVariant.objects.order_by('position'),
            ),
        )
        if any(
            [link.variant_id for link in match.variant_links.all()] == variant_ids
            for match in matches
        ):
            continue
        saved = Language.objects.create(
            primary_language=language,
            extlang=extended,
            script=script,
            region=region,
        )
        LanguageVariant.objects.bulk_create(
            [
                LanguageVariant(
                    language=saved, variant_id=variant_id, position=position
                )
                for position, variant_id in enumerate(variant_ids)
            ],
        )


@transaction.atomic
def sync_database(paths: dict[str, Path]) -> None:
    """
    Import the locale datasets as an atomic, repeatable update.
    """
    registry = read_registry(paths['iana'])
    countries = upsert(
        Country,
        [
            Country(
                alpha2=row['alpha2_code'],
                alpha3=row['alpha3_code'],
                numeric_code=row['numeric_code'],
                name=row['short_name_lower_case'] or row['short_name'],
                name_full=row['full_name'] or '',
            )
            for row in read_rows(paths['iso-3166-1'], 'countries')
        ],
        'alpha2',
        'alpha3',
        'numeric_code',
        'name',
        'name_full',
    )
    script_names = {
        row['code']: row['name_en'] for row in read_rows(paths['iso-15924'], 'scripts')
    }
    scripts = upsert(
        ScriptSubtag,
        [
            ScriptSubtag(
                code=code,
                name=script_names.get(code) or registry_value(record, 'Description'),
                deprecated_on=deprecation_date(record),
            )
            for code, record in registry.get('script', {}).items()
        ],
        'code',
        'name',
        'deprecated_on',
    )
    numeric_countries = {
        country.numeric_code: country for country in countries.values()
    }
    region_names = m49_names(read_rows(paths['un-m-49'], 'countries'))
    regions = upsert(
        RegionSubtag,
        [
            RegionSubtag(
                code=code,
                name=region_names.get(code) or registry_value(record, 'Description'),
                deprecated_on=deprecation_date(record),
                country=countries.get(code) or numeric_countries.get(code),
            )
            for code, record in registry.get('region', {}).items()
        ],
        'code',
        'name',
        'deprecated_on',
        'country',
    )
    variants = upsert(
        VariantSubtag,
        [
            VariantSubtag(
                code=code,
                name=registry_value(record, 'Description'),
                deprecated_on=deprecation_date(record),
            )
            for code, record in registry.get('variant', {}).items()
        ],
        'code',
        'name',
        'deprecated_on',
    )
    primary = sync_primary_languages(registry['language'], paths, scripts)
    ExtendedLanguageSubtag.objects.bulk_create(
        [
            ExtendedLanguageSubtag(
                language=primary[code],
                prefix=primary[registry_value(record, 'Prefix')],
                scope=language_scope(record),
            )
            for code, record in registry.get('extlang', {}).items()
        ],
        update_conflicts=True,
        update_fields=[
            'prefix',
            'scope',
        ],
        unique_fields=[
            'language',
        ],
    )
    extlangs = ExtendedLanguageSubtag.objects.in_bulk(field_name='language_id')
    sync_language_tags(registry, primary, extlangs, scripts, regions, variants)
