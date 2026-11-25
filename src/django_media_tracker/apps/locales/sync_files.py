"""
Download and parse published country, language, and script datasets.
"""

import csv
import json
import re
from collections.abc import Callable
from html.parser import HTMLParser
from io import StringIO
from urllib.request import Request
from urllib.request import urlopen

ISO_COUNTRY_ASSIGNMENTS_URL = (
    'https://salsa.debian.org/iso-codes-team/iso-codes/-/raw/main/data/iso_3166-1.json'
)
ISO_COUNTRY_DETAILS_URL = 'https://raw.githubusercontent.com/lbajada/iso3166-scraper/main/countries/countries.json'
ISO_COUNTRY_NAMES_URL = (
    'https://raw.githubusercontent.com/inwebo/iso-3166-dataset/master/iso-3166-dataset'
)
M49_URL = 'https://unstats.un.org/unsd/methodology/m49/overview/'
ISO_639_2_URL = 'https://www.loc.gov/standards/iso639-2/ISO-639-2_utf-8.txt'
ISO_639_3_URL = 'https://iso639-3.sil.org/sites/iso639-3/files/downloads/iso-639-3.tab'
ISO_639_5_URL = 'https://www.loc.gov/standards/iso639-5/id.php'
ISO_15924_URL = 'https://www.unicode.org/iso15924/iso15924.txt'
IANA_URL = (
    'https://www.iana.org/assignments/language-subtag-registry/language-subtag-registry'
)

Download = Callable[[str], bytes]


def download(url: str) -> bytes:
    """
    Fetch the current published contents with a bounded network timeout.
    """
    request = Request(
        url,
        headers={
            'User-Agent': 'django-media-tracker/locale-sync',
            'Cache-Control': 'no-cache',
        },
    )
    with urlopen(request, timeout=30) as response:
        return response.read()


def encode_json(
    key: str,
    records: list[dict[str, object]],
    *,
    notes: dict[str, str] | None = None,
) -> bytes:
    """
    Serialize nonempty datasets as UTF-8 JSON.
    """
    if not records:
        raise ValueError(f'No {key} records found.')
    payload: dict[str, object] = {
        key: records,
    }
    if notes:
        payload['notes'] = notes
    data = json.dumps(payload, ensure_ascii=False, indent=2)
    return f'{data}\n'.encode()


def load_iso_countries(fetch: Download) -> bytes:
    """
    Combine the active country assignments with public OBP and bilingual data.
    """
    assignments = json.loads(fetch(ISO_COUNTRY_ASSIGNMENTS_URL))['3166-1']
    snapshot = json.loads(fetch(ISO_COUNTRY_DETAILS_URL))['countries']
    details = {
        row['alpha2_code']: row
        for row in snapshot
        if row['status'] == 'Officially assigned'
    }
    # The public OBP snapshot currently omits the assigned French Guiana entry.
    english = load_country_names(fetch, 'EN')
    french = load_country_names(fetch, 'FR')
    columns = {key for row in details.values() for key in row}
    if not columns:
        raise ValueError('No assigned country details found in the OBP snapshot.')
    countries = []
    for entry in sorted(assignments, key=lambda row: row['alpha_2']):
        code = entry['alpha_2']
        alpha3 = entry['alpha_3']
        numeric = entry['numeric']
        expected_codes = (
            alpha3,
            numeric,
        )
        if code in details:
            row = details[code].copy()
            details_codes = (
                row['alpha3_code'],
                str(row['numeric_code']).zfill(3),
            )
        else:
            fallback = english[code]
            details_codes = (
                fallback['Alpha-3'],
                fallback['Numeric'],
            )
            row = dict.fromkeys(sorted(columns))
            row.update(
                alpha2_code=code,
                alpha3_code=alpha3,
                short_name=entry['name'].upper(),
                short_name_lower_case=entry['name'],
                independent='Yes' if fallback['Independent'] == 'true' else 'No',
                remarks=fallback['Remarks'] or None,
                status='Officially assigned',
            )
        translated = french[code]
        french_codes = (
            translated['Alpha-3'],
            translated['Code numérique'],
        )
        if details_codes != expected_codes or french_codes != expected_codes:
            raise ValueError(f'Country sources disagree on the codes for {code}.')
        row.update(
            numeric_code=numeric,
            short_name_fr=translated['Nom court'],
            short_name_lower_case_fr=translated['Nom court minuscule'],
            full_name_fr=translated['Nom complet'] or None,
            remarks_fr=translated['Remarques'] or None,
        )
        countries.append(row)
    return encode_json('countries', countries)


def load_country_names(fetch: Download, language: str) -> dict[str, dict[str, str]]:
    """
    Index the published bilingual country tables by alpha-2 code.
    """
    data = fetch(f'{ISO_COUNTRY_NAMES_URL}-{language}.csv').decode('utf-8-sig')
    return {row['Alpha-2']: row for row in csv.DictReader(StringIO(data))}


class CodeTable(HTMLParser):
    """
    Extract cells from a published code table identified by its HTML attributes.
    """

    def __init__(self, attribute: str, value: str) -> None:
        """
        Select the table by its id or class.
        """
        super().__init__()
        self.attribute = attribute
        self.value = value
        self.rows: list[list[str]] = []
        self.in_table = False
        self.row: list[str] = []
        self.spanned_row = False
        self.cell: list[str] | None = None
        self.notes: dict[str, str] = {}
        self.note_id: str | None = None
        self.note_start = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """
        Begin collecting rows or cells from the selected table.
        """
        if tag == 'table' and dict(attrs).get(self.attribute) == self.value:
            self.in_table = True
        elif self.in_table:
            if tag == 'tr':
                self.row = []
                self.spanned_row = False
            elif tag in ('th', 'td'):
                self.cell = []
                self.spanned_row |= 'colspan' in dict(attrs)
            elif tag == 'li' and self.spanned_row and self.cell is not None:
                self.note_id = dict(attrs).get('id')
                self.note_start = len(self.cell)
            elif tag in ('br', 'div') and self.cell is not None:
                self.cell.append('\n')

    def handle_data(self, data: str) -> None:
        """
        Preserve the text contained in the current cell.
        """
        if self.cell is not None:
            self.cell.append(data)

    def handle_endtag(self, tag: str) -> None:
        """
        Store completed cells and rows.
        """
        if not self.in_table:
            return
        if tag == 'li' and self.note_id is not None and self.cell is not None:
            self.notes[self.note_id] = ''.join(self.cell[self.note_start :]).strip()
            self.note_id = None
        elif tag in ('th', 'td') and self.cell is not None:
            self.row.append(''.join(self.cell).strip())
            self.cell = None
        elif tag == 'tr' and self.row and not self.spanned_row:
            self.rows.append(self.row)
        elif tag == 'table':
            self.in_table = False


def load_html_table(
    content: bytes,
    attribute: str,
    value: str,
    columns: tuple[str, ...],
) -> tuple[list[dict[str, object]], dict[str, str]]:
    """
    Parse a code table with the expected number of columns.
    """
    table = CodeTable(attribute, value)
    table.feed(content.decode('utf-8-sig'))
    rows = [dict(zip(columns, row, strict=True)) for row in table.rows[1:]]
    return rows, table.notes


def load_m49_countries(fetch: Download) -> bytes:
    """
    Preserve every column in the UN's English M49 overview table.
    """
    columns = (
        'global_code',
        'global_name',
        'region_code',
        'region_name',
        'subregion_code',
        'subregion_name',
        'intermediate_region_code',
        'intermediate_region_name',
        'country_or_area',
        'm49_code',
        'iso_alpha2_code',
        'iso_alpha3_code',
        'least_developed_countries',
        'landlocked_developing_countries',
        'small_island_developing_states',
    )
    records, _ = load_html_table(fetch(M49_URL), 'id', 'downloadTableEN', columns)
    return encode_json('countries', records)


def load_iso_languages(fetch: Download, *, alpha2_only: bool = False) -> bytes:
    """
    Read Set 2 and derive Set 1 from the records with an alpha-2 code.
    """
    records: list[dict[str, object]] = []
    for line in fetch(ISO_639_2_URL).decode('utf-8-sig').splitlines():
        if not line.strip():
            continue
        bibliographic, terminological, alpha2, english, french = line.split('|')
        if not alpha2_only or alpha2:
            records.append(
                {
                    'alpha2': alpha2 or None,
                    'alpha3_bibliographic': bibliographic,
                    'alpha3_terminological': terminological or bibliographic,
                    'name_en': english,
                    'name_fr': french,
                },
            )
    return encode_json('languages', records)


def load_iso_639_3(fetch: Download) -> bytes:
    """
    Preserve all columns from SIL's ISO 639-3 code table.
    """
    data = fetch(ISO_639_3_URL).decode('utf-8-sig')
    reader = csv.DictReader(StringIO(data), delimiter='\t')
    if not reader.fieldnames or reader.fieldnames[0] != 'Id':
        raise ValueError('Invalid ISO 639-3 table header.')
    records = [
        {key.lower(): value or None for key, value in row.items()} for row in reader
    ]
    return encode_json('languages', records)


def load_iso_639_5(fetch: Download) -> bytes:
    """
    Preserve bilingual names, hierarchy, and notes from the Set 5 table.
    """
    columns = (
        'alpha3',
        'name_en',
        'name_fr',
        'iso_639_2',
        'hierarchy',
        'notes',
    )
    records, notes = load_html_table(
        fetch(ISO_639_5_URL), 'class', 'Dynamic639-5OutputTables', columns
    )
    return encode_json('languages', records, notes=notes)


def load_iso_scripts(fetch: Download) -> bytes:
    """
    Preserve all published ISO 15924 script columns.
    """
    columns = (
        'code',
        'numeric',
        'name_en',
        'name_fr',
        'property_value_alias',
        'unicode_version',
        'date',
    )
    records = [
        dict(zip(columns, line.split(';'), strict=True))
        for line in fetch(ISO_15924_URL).decode('utf-8-sig').splitlines()
        if line.strip() and not line.startswith('#')
    ]
    return encode_json('scripts', records)


def load_iana_registry(fetch: Download) -> bytes:
    """
    Preserve the registry text byte for byte after checking its header.
    """
    contents = fetch(IANA_URL)
    text = contents.decode('utf-8')
    if not re.match(r'File-Date: [0-9]{4}-[0-9]{2}-[0-9]{2}\r?\n%%\r?\n', text):
        raise ValueError('Invalid IANA language subtag registry header.')
    return contents
