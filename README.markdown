# Django Media Tracker

A starter Django project with Django REST Framework, SQLite, and Django admin.
The media app is registered and ready for collection models.
The locales app manages reference files for countries, languages, and scripts.

## Local development

Use Python 3.11 or newer. Run these commands from the repository root.

```sh
make venv.install
make data.migrate
make run
```

`make run` starts Django at `http://127.0.0.1:8000/` using the project
virtual environment. It enables debug mode and generates a temporary
secret key by default. Set `DJANGO_DEBUG` or `DJANGO_SECRET_KEY` to
override those defaults.

`make data.migrate` applies pending migrations to the local SQLite database
at `src/db.sqlite3`. It generates a temporary secret key if
`DJANGO_SECRET_KEY` is unset. Set `DJANGO_DATABASE_PATH` to use another
local database file. Keep the database out of source control.

After changing models, run `make data.migrations` to generate migration
files. Review the generated files before applying them with
`make data.migrate`.

`make venv` creates `.venv` if needed. `make venv.install` also installs
the runtime and development dependencies into it. The Django commands
above run the application directly from `src/`. Set `BOOTSTRAP_PYTHON`
when creating the environment to choose a Python other than `python3`.

Send a GET request to `http://127.0.0.1:8000/api/health/` for
`{"status": "ok"}`. The endpoint checks that the API responds and does not
query the database. To create an account for
`http://127.0.0.1:8000/admin/`, run these commands after applying migrations.

```sh
source .venv/bin/activate
export DJANGO_SECRET_KEY="$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')"
python src/manage.py createsuperuser
```

`DJANGO_SECRET_KEY` is required for direct Django commands. Django settings
enable debug mode when `DJANGO_DEBUG=1`.
Set `DJANGO_ALLOWED_HOSTS` to a space-separated list of hostnames when
running with debug mode off.

## Development data

- `make data.export` exports the development database as a Django JSON
  fixture at `var/django-db.json`, creating `var/` as needed.
- `make data.import` loads that fixture into the development database.
  It first copies the existing SQLite file to `var/django-db.sqlite3`.
  Run `make data.migrate` first and stop the development server before
  importing so the file is idle during the copy. For a clean restore, use
  a fresh database because importing can update matching records and
  leaves unrelated records in place.

Both targets honor `DJANGO_DATABASE_PATH`. The fixture can contain user data
and password hashes and is kept out of source control.

## Locale reference files

Manage countries, language tags, and subtags under **Locales** in Django
Admin. The language tag form also lets you edit its variants and extensions.

After installing the development dependencies and setting
`DJANGO_SECRET_KEY`, run the sync command from the repository root.

```sh
.venv/bin/python -B src/manage.py locale_sync_files
```

It refreshes eight files in `etc/`. Use `--help` to see the destination
options, such as `--un-m-49-path /tmp/country_un-m-49.json`. A download or
parsing failure preserves the affected file, and the command still attempts
the other datasets before reporting errors.

The ISO country JSON combines public country datasets and preserves their
available attributes. ISO 639-1 is derived from alpha-2 entries in the ISO
639-2 table. UN M49 uses the English overview table, and the IANA registry
is saved as published.

The `locales` models store ISO 3166-1 countries and structured BCP 47 tags.
A tag links to a primary language and can add an extlang, script, region,
ordered variants, extensions, and a private-use suffix. Numeric UN M49
regions can stand on their own, as in `es-419`. Primary subtags can record
their ISO 639-3 language type and IANA deprecation date. Primary and
extended subtags store IANA scope, defaulting to `individual` when
`Scope:` is absent. Rerun `locale_sync_db` after migrating to refresh
scope on existing records.

Run `make data.migrate` to create the tables, then import the synced files
with `.venv/bin/python -B src/manage.py locale_sync_db`. The import uses
the same path options and defaults as `locale_sync_files`. It refreshes
countries and registered subtags, seeds current primary tags and structured
IANA whole tags, and preserves unrelated rows. If any input fails, the
database changes roll back. The schema covers tags with a primary language,
with legacy whole tags and private-use-only tags outside its scope.

## Checks

Run `make test` from the repository root after `make venv.install`.
It uses `.venv` directly to format Python files, run Ruff lint checks,
and run the Django test suite. The suite uses an in-memory SQLite database
and a temporary secret key by default.
Run `make test.format`, `make test.lint`, or `make test.python` to run a
single step.

GitHub Actions runs the same Make targets on pull requests across the
supported Python, Debian, and Ubuntu versions.
