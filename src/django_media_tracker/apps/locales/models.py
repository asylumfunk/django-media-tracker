"""
Store ISO countries and the components of structured BCP 47 language tags.
"""

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models


class Country(models.Model):
    """
    Identify an ISO 3166-1 country or territory.
    """

    name = models.CharField(max_length=255)
    name_full = models.CharField(max_length=255, blank=True)
    alpha2 = models.CharField(
        max_length=2,
        unique=True,
        validators=[
            RegexValidator(r'\A[A-Z]{2}\Z'),
        ],
    )
    alpha3 = models.CharField(
        max_length=3,
        unique=True,
        validators=[
            RegexValidator(r'\A[A-Z]{3}\Z'),
        ],
    )
    numeric_code = models.CharField(
        max_length=3,
        unique=True,
        validators=[
            RegexValidator(r'\A[0-9]{3}\Z'),
        ],
    )

    def __str__(self) -> str:
        """
        Return the English short name.
        """
        return self.name


class RegisteredSubtag(models.Model):
    """
    Share the display and registration metadata of IANA subtags.
    """

    name = models.CharField(max_length=255)
    added_on = models.DateField(blank=True, null=True)
    deprecated_on = models.DateField(blank=True, null=True)

    class Meta:
        """
        Keep shared fields on the concrete subtag tables.
        """

        abstract = True

    def __str__(self) -> str:
        """
        Return the subtag in its customary casing.
        """
        return self.code


class ScriptSubtag(RegisteredSubtag):
    """
    Represent an IANA script subtag based on an ISO 15924 code.
    """

    code = models.CharField(
        max_length=4,
        unique=True,
        validators=[
            RegexValidator(r'\A[A-Z][a-z]{3}\Z'),
        ],
    )


class LanguageScope(models.TextChoices):
    """
    Classify a language subtag using the IANA registry's scope values.
    """

    INDIVIDUAL = 'individual', 'Individual'
    MACROLANGUAGE = 'macrolanguage', 'Macrolanguage'
    COLLECTION = 'collection', 'Collection'
    SPECIAL = 'special', 'Special'
    PRIVATE_USE = 'private-use', 'Private use'


class PrimaryLanguageSubtag(RegisteredSubtag):
    """
    Represent an IANA primary language subtag and its ISO 639-3 classification.
    """

    class LanguageType(models.TextChoices):
        """
        Preserve the language type codes from ISO 639-3.
        """

        ANCIENT = 'A', 'Ancient'
        CONSTRUCTED = 'C', 'Constructed'
        EXTINCT = 'E', 'Extinct'
        HISTORICAL = 'H', 'Historical'
        LIVING = 'L', 'Living'
        SPECIAL = 'S', 'Special'

    code = models.CharField(
        max_length=8,
        unique=True,
        validators=[
            RegexValidator(r'\A[a-z]{2,8}\Z'),
        ],
    )
    language_type = models.CharField(max_length=1, choices=LanguageType, blank=True)
    scope = models.CharField(
        max_length=13,
        choices=LanguageScope,
        default=LanguageScope.INDIVIDUAL,
    )
    suppress_script = models.ForeignKey(
        ScriptSubtag,
        on_delete=models.PROTECT,
        related_name='languages_with_suppressed_script',
        blank=True,
        null=True,
    )
    macrolanguage = models.ForeignKey(
        'self',
        on_delete=models.PROTECT,
        related_name='encompassed_languages',
        blank=True,
        null=True,
    )


class ExtendedLanguageSubtag(models.Model):
    """
    Link an extlang to its equivalent primary subtag and its required prefix.
    """

    language = models.OneToOneField(
        PrimaryLanguageSubtag,
        on_delete=models.PROTECT,
        related_name='extended_form',
    )
    prefix = models.ForeignKey(
        PrimaryLanguageSubtag,
        on_delete=models.PROTECT,
        related_name='extended_subtags',
    )
    added_on = models.DateField(blank=True, null=True)
    scope = models.CharField(
        max_length=13,
        choices=LanguageScope,
        default=LanguageScope.INDIVIDUAL,
    )

    def clean(self) -> None:
        """
        Require the extlang's equivalent primary code to be three letters.
        """
        super().clean()
        if (
            PrimaryLanguageSubtag.objects.filter(pk=self.language_id)
            .exclude(
                code__regex=r'^[a-z]{3}$',
            )
            .exists()
        ):
            raise ValidationError(
                {
                    'language': 'The extlang needs a three-letter code.',
                },
            )

    def __str__(self) -> str:
        """
        Return the extlang code shared with its primary subtag.
        """
        return self.language.code


class RegionSubtag(RegisteredSubtag):
    """
    Represent an IANA region subtag based on ISO 3166-1 or UN M49.
    """

    code = models.CharField(
        max_length=3,
        unique=True,
        validators=[
            RegexValidator(r'\A(?:[A-Z]{2}|[0-9]{3})\Z'),
        ],
    )
    country = models.ForeignKey(
        Country,
        on_delete=models.PROTECT,
        related_name='region_subtags',
        blank=True,
        null=True,
    )

    def clean(self) -> None:
        """
        Verify the code matches the country when a country is supplied.
        """
        super().clean()
        if (
            Country.objects.filter(pk=self.country_id)
            .exclude(
                models.Q(alpha2=self.code) | models.Q(numeric_code=self.code),
            )
            .exists()
        ):
            raise ValidationError(
                {
                    'country': 'The country does not match this region code.',
                },
            )


class VariantSubtag(RegisteredSubtag):
    """
    Represent an IANA variant subtag.
    """

    code = models.CharField(
        max_length=8,
        unique=True,
        validators=[
            RegexValidator(r'\A(?:[a-z0-9]{5,8}|[0-9][a-z0-9]{3})\Z'),
        ],
    )


class Language(models.Model):
    """
    Compose a BCP 47 tag from registered subtags and optional suffixes.
    """

    primary_language = models.ForeignKey(
        PrimaryLanguageSubtag,
        on_delete=models.PROTECT,
        related_name='language_tags',
    )
    extlang = models.ForeignKey(
        ExtendedLanguageSubtag,
        on_delete=models.PROTECT,
        related_name='language_tags',
        blank=True,
        null=True,
    )
    script = models.ForeignKey(
        ScriptSubtag,
        on_delete=models.PROTECT,
        related_name='language_tags',
        blank=True,
        null=True,
    )
    region = models.ForeignKey(
        RegionSubtag,
        on_delete=models.PROTECT,
        related_name='language_tags',
        blank=True,
        null=True,
    )
    variants = models.ManyToManyField(
        VariantSubtag,
        through='LanguageVariant',
        related_name='language_tags',
        blank=True,
    )
    private_use = models.CharField(
        max_length=255,
        blank=True,
        validators=[
            RegexValidator(r'\A[a-z0-9]{1,8}(?:-[a-z0-9]{1,8})*\Z'),
        ],
        help_text='Private-use subtags without the x- prefix.',
    )
    added_on = models.DateField(
        blank=True,
        null=True,
        help_text='IANA registration date for this whole tag, when available.',
    )

    def clean(self) -> None:
        """
        Require the primary language to match the extlang's registered prefix.
        """
        super().clean()
        if (
            ExtendedLanguageSubtag.objects.filter(pk=self.extlang_id)
            .exclude(
                prefix_id=self.primary_language_id,
            )
            .exists()
        ):
            raise ValidationError(
                {
                    'extlang': 'This extlang requires a different prefix.',
                },
            )

    @property
    def tag(self) -> str:
        """
        Render the tag using conventional subtag casing and order.
        """
        parts = [
            self.primary_language.code,
        ]
        if self.extlang_id:
            parts.append(self.extlang.language.code)
        if self.script_id:
            parts.append(self.script.code)
        if self.region_id:
            parts.append(self.region.code)
        if not self._state.adding:
            parts.extend(
                self.variant_links.order_by('position').values_list(
                    'variant__code', flat=True
                ),
            )
            parts.extend(
                str(extension) for extension in self.extensions.order_by('singleton')
            )
        if self.private_use:
            parts.append(f'x-{self.private_use}')
        return '-'.join(parts)

    def __str__(self) -> str:
        """
        Return the assembled BCP 47 tag.
        """
        return self.tag


class LanguageVariant(models.Model):
    """
    Attach a variant to a language tag at a specific position.
    """

    language = models.ForeignKey(
        Language,
        on_delete=models.CASCADE,
        related_name='variant_links',
    )
    variant = models.ForeignKey(
        VariantSubtag,
        on_delete=models.PROTECT,
        related_name='language_links',
    )
    position = models.PositiveIntegerField()

    class Meta:
        """
        Prevent duplicate variants and positions within the same tag.
        """

        constraints = [
            models.UniqueConstraint(
                fields=[
                    'language',
                    'variant',
                ],
                name='locales_language_variant_unique',
            ),
            models.UniqueConstraint(
                fields=[
                    'language',
                    'position',
                ],
                name='locales_language_variant_position_unique',
            ),
        ]


class LanguageExtension(models.Model):
    """
    Attach an extension sequence to a language tag by its singleton.
    """

    language = models.ForeignKey(
        Language,
        on_delete=models.CASCADE,
        related_name='extensions',
    )
    singleton = models.CharField(
        max_length=1,
        validators=[
            RegexValidator(r'\A[0-9a-wy-z]\Z'),
        ],
    )
    value = models.CharField(
        max_length=255,
        validators=[
            RegexValidator(r'\A[a-z0-9]{2,8}(?:-[a-z0-9]{2,8})*\Z'),
        ],
    )

    class Meta:
        """
        Allow each extension singleton at most once per tag.
        """

        constraints = [
            models.UniqueConstraint(
                fields=[
                    'language',
                    'singleton',
                ],
                name='locales_language_extension_singleton_unique',
            ),
        ]

    def __str__(self) -> str:
        """
        Return the extension with its leading singleton.
        """
        return f'{self.singleton}-{self.value}'
