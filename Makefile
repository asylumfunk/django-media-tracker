.DEFAULT_GOAL := test

VENV := .venv
PYTHON := $(VENV)/bin/python
BOOTSTRAP_PYTHON ?= python3
LOCAL_SECRET_KEY = "$${DJANGO_SECRET_KEY:-$$("$(PYTHON)" -B -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')}"
DATA_FILE := var/django-db.json

.PHONY: venv venv.install run migrate data.export data.import test test.lint test.format test.python

venv:
	@if [ ! -x "$(PYTHON)" ]; then $(BOOTSTRAP_PYTHON) -m venv "$(VENV)"; fi

venv.install: venv
	"$(PYTHON)" -m pip install -r requirements-dev.txt

run:
	DJANGO_DEBUG="$${DJANGO_DEBUG:-1}" \
	DJANGO_SECRET_KEY=$(LOCAL_SECRET_KEY) \
	"$(PYTHON)" -B src/manage.py runserver

migrate:
	DJANGO_SECRET_KEY=$(LOCAL_SECRET_KEY) "$(PYTHON)" -B src/manage.py migrate

data.export:
	@mkdir -p "$(dir $(DATA_FILE))"
	@set -e; \
	fixture=$$(mktemp "$(DATA_FILE).XXXXXX"); \
	trap 'rm -f "$$fixture"' EXIT; \
	DJANGO_SECRET_KEY=$(LOCAL_SECRET_KEY) "$(PYTHON)" -B src/manage.py dumpdata \
		--all --natural-foreign --natural-primary --indent 2 --output "$$fixture"; \
	mv -f "$$fixture" "$(DATA_FILE)"

data.import:
	DJANGO_SECRET_KEY=$(LOCAL_SECRET_KEY) "$(PYTHON)" -B src/manage.py loaddata "$(DATA_FILE)"

test:
	$(MAKE) test.format
	$(MAKE) test.lint
	$(MAKE) test.python

test.lint:
	"$(PYTHON)" -m ruff check --no-cache src/

test.format:
	"$(PYTHON)" -m ruff format --no-cache src/

test.python:
	DJANGO_DATABASE_PATH="$${DJANGO_DATABASE_PATH:-:memory:}" \
	DJANGO_SECRET_KEY=$(LOCAL_SECRET_KEY) \
	"$(PYTHON)" -B src/manage.py test django_media_tracker
