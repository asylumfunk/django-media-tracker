.DEFAULT_GOAL := test

VENV := .venv
PYTHON := $(VENV)/bin/python
BOOTSTRAP_PYTHON ?= python3
LOCAL_SECRET_KEY = "$${DJANGO_SECRET_KEY:-$$("$(PYTHON)" -B -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')}"

.PHONY: venv venv.install run migrate test test.lint test.format test.python

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

test:
	$(MAKE) test.format
	$(MAKE) test.lint
	$(MAKE) test.python

test.lint:
	"$(PYTHON)" -m ruff check --no-cache src/

test.format:
	"$(PYTHON)" -m ruff format --no-cache src/

test.python:
	"$(PYTHON)" -B src/manage.py test django_media_tracker
