# Django Media Tracker

A starter Django project with Django REST Framework, SQLite, and Django admin.
The media app is registered and ready for collection models.

## Local development

Use Python 3.11 or newer. Run these commands from the repository root.

```sh
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt

export DJANGO_SECRET_KEY="$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')"
export DJANGO_DEBUG=1

python src/manage.py migrate
python src/manage.py runserver
```

Send a GET request to `http://127.0.0.1:8000/api/health/` for
`{"status": "ok"}`. The endpoint checks that the API responds and does not
query the database. To sign in at `http://127.0.0.1:8000/admin/`, first run
`python src/manage.py createsuperuser`.

`DJANGO_SECRET_KEY` is required. Debug mode is off unless `DJANGO_DEBUG=1`.
Set `DJANGO_ALLOWED_HOSTS` to a space-separated list of hostnames when
running with debug mode off. SQLite defaults to `src/db.sqlite3`.
Set `DJANGO_DATABASE_PATH` to use another path.

## Checks

```sh
python src/manage.py test django_media_tracker
ruff check src/
ruff format --check src/
```

Put docstring opening and closing triple double quotes on their own lines.
Start the summary on the line after the opening quotes. Ruff checks the
quotes and summary placement for multiline docstrings. The Django test
suite also checks for single-line docstrings in Python files listed by Git.
