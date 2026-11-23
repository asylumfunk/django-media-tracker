# Django Media Tracker

A starter Django project with Django REST Framework, SQLite, and Django admin.
The media app is registered and ready for collection models.

## Local development

Use Python 3.11 or newer. Run these commands from the repository root.

```sh
make venv.install
make migrate
make run
```

`make run` starts Django at `http://127.0.0.1:8000/` using the project
virtual environment. It enables debug mode and generates a temporary
secret key by default. Set `DJANGO_DEBUG` or `DJANGO_SECRET_KEY` to
override those defaults.

`make migrate` applies pending migrations to the local SQLite database
at `src/db.sqlite3`. It generates a temporary secret key if
`DJANGO_SECRET_KEY` is unset. Set `DJANGO_DATABASE_PATH` to use another
local database file. Keep the database out of source control.

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

## Checks

Run `make test` from the repository root after `make venv.install` and
setting `DJANGO_SECRET_KEY` as shown above. It uses `.venv` directly and reformats
Python files, runs Ruff lint checks, and then runs the Django test suite.
Run `make test.format`, `make test.lint`, or `make test.python` to run a
single step.
