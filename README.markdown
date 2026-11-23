# Django Media Tracker

A starter Django project with Django REST Framework, SQLite, and Django admin.
The media app is registered and ready for collection models.

## Local development

Use Python 3.11 or newer. Run these commands from the repository root.

```sh
make venv.install
source .venv/bin/activate

export DJANGO_SECRET_KEY="$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')"
export DJANGO_DEBUG=1

python src/manage.py migrate
python src/manage.py runserver
```

`make venv` creates `.venv` if needed. `make venv.install` also installs
the runtime and development dependencies into it. The Django commands
above run the application directly from `src/`. Set `BOOTSTRAP_PYTHON`
when creating the environment to choose a Python other than `python3`.

Send a GET request to `http://127.0.0.1:8000/api/health/` for
`{"status": "ok"}`. The endpoint checks that the API responds and does not
query the database. To sign in at `http://127.0.0.1:8000/admin/`, first run
`python src/manage.py createsuperuser`.

`DJANGO_SECRET_KEY` is required. Debug mode is off unless `DJANGO_DEBUG=1`.
Set `DJANGO_ALLOWED_HOSTS` to a space-separated list of hostnames when
running with debug mode off. SQLite defaults to `src/db.sqlite3`.
Set `DJANGO_DATABASE_PATH` to use another path.

## Checks

Run `make test` from the repository root after `make venv.install` and
setting `DJANGO_SECRET_KEY` as shown above. It uses `.venv` directly and reformats
Python files, runs Ruff lint checks, and then runs the Django test suite.
Run `make test.format`, `make test.lint`, or `make test.python` to run a
single step.
