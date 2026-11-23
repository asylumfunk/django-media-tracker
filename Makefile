.PHONY: test test.lint test.format test.python

test:
	$(MAKE) test.format
	$(MAKE) test.lint
	$(MAKE) test.python

test.lint:
	ruff check --no-cache src/

test.format:
	ruff format --no-cache src/

test.python:
	python -B src/manage.py test django_media_tracker
