# AGENTS.md

## Project Overview

This project is a Python web application built with Django and Django REST
Framework (DRF).

The Django project is named `django_media_tracker`.

## Project Structure

### High-level

- By default, follow established Python, Django, and Django REST Framework
  conventions.
- Otherwise, follow existing project conventions unless they conflict with
  these instructions.
- Prioritize readability, maintainability, security, testability, and
  simplicity.

### Layout

Use the following project structure as the architectural convention:

```text
django-media-tracker/
├── AGENTS.md
├── README.markdown
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
├── .gitignore
└── src/
    ├── manage.py
    ├── django_media_tracker/
    │   ├── __init__.py
    │   ├── settings.py
    │   ├── urls.py
    │   ├── asgi.py
    │   ├── wsgi.py
    │   ├── apps/
    │   │   ├── __init__.py
    │   │   ├── media/
    │   │   │   ├── __init__.py
    │   │   │   ├── apps.py
    │   │   │   ├── models.py
    │   │   │   ├── admin.py
    │   │   │   ├── serializers.py
    │   │   │   ├── views.py
    │   │   │   ├── urls.py
    │   │   │   ├── tests/
    │   │   │   │   ├── __init__.py
    │   │   │   │   ├── test_models.py
    │   │   │   │   ├── test_serializers.py
    │   │   │   │   └── test_views.py
    │   │   │   └── migrations/
    │   │   │       └── __init__.py
    │   │   └── ...
    │   ├── common/
    │   │   ├── __init__.py
    │   │   └── ...
    │   ├── tests/
    │   │   ├── __init__.py
    │   │   └── ...
```

### Source Code Organization

- All Python files must be located under `src/`.
- Do not create Python modules or packages in the repository root.
- The Django project configuration package must be named
  `django_media_tracker`.
- Django project configuration belongs in `src/django_media_tracker/`.
- All Django applications must reside in `src/django_media_tracker/apps/`.
- Register applications using their complete Python package paths, such as
  `django_media_tracker.apps.media`.
- Keep shared application-independent functionality in
  `src/django_media_tracker/common/`.
- Avoid unnecessary packages or abstraction layers.
- Keep each Django application focused on a clearly defined responsibility.
- Avoid circular dependencies between applications.

### Tests

- Tests must be stored under `src/`.
    - Do not create a top-level `tests/` directory outside `src/`.
- Place tests alongside the code they exercise.
- Prefer a `tests/` subdirectory within each Django application.
- Place project-level tests in `src/django_media_tracker/tests/`.
- Name test modules using the `test_*.py` convention.
- Organize tests by the component being tested.
- Keep tests independent, deterministic, and repeatable.
- Write tests for all new code; set a goal of 100% test coverage.

## Python Coding Standards

### General Conventions

- Follow PEP 8.
- Use descriptive names for variables, functions, classes, and modules.
- Prefer explicit, readable code over clever or unnecessarily compact
  implementations.
- Keep functions and classes focused on a single responsibility.
- Avoid unnecessary abstractions and premature optimization.
- Prefer composition over inheritance when appropriate.
- Use context managers when working with resources.
- Avoid global mutable state.
- Avoid mutable default arguments.

### Collection Formatting

- Write non-empty collection literals across multiple lines, with one item
  per line and the closing delimiter on its own line. Include a trailing
  comma after the final item where the syntax supports it.
- Write empty collections on a single line.
- Apply the same layout to TOML arrays. Use standard TOML tables for
  non-empty mappings so each entry can be on its own line.

### Libaries

- Use standard library functionality whenever practical.
- Use `pathlib` instead of `os.path` for filesystem operations where practical.

#### Imports

Import only a single object from each from/import statement.

Examples:

```python
from rest_framework.decorators import api_view
from rest_framework.decorators import germission_classes
```

### String Quoting

Use the following quoting conventions consistently:

- Use single quotes (`'`) for ordinary strings.
- Use double quotes (`"`) for f-strings.
- Use double quotes for other interpolated strings.
- Use double quotes when necessary to avoid escaping embedded single quotes.
- Use triple-quoted strings for docstrings.

Examples:

```python
name = 'media_tracker'
message = f"Processing {name}"

query = 'SELECT * FROM media'
description = "The user's media collection"

def get_message(username: str) -> str:
    return f"Welcome, {username}!"
```

Configure formatting and linting tools to respect these conventions.

### Type Hints

- Use type hints for function parameters and return values.
- Use appropriate types for class attributes and public APIs.
- Prefer precise types over `Any`.
- Use modern Python typing syntax when supported by the configured Python
  version.
- Avoid unnecessary type complexity.

### Error Handling

- Handle exceptions explicitly.
- Avoid bare `except` clauses.
- Avoid silently swallowing exceptions.
    - Raise meaningful exceptions when appropriate.
- Avoid using exceptions for ordinary control flow.
- Never expose internal exception details to API consumers.

### Documentation

- Use docstrings for public classes, functions, and modules.
- Document non-obvious behavior and architectural decisions.
    - Link to external documentation sources when relevant.
- Prefer comments that explain why something is necessary rather than restating
  what the code does.

#### Docstrings

- Use triple double quotes
- Put docstring opening and closing double quotes on their own lines.
    - Start the summary on the line after the opening quotes.
- Ruff checks the quotes and summary placement for multiline docstrings.
- The Django test suite also checks for single-line docstrings in Python
  files listed by Git.

Examples:

```python
"""
Format docstrings to always be multiple lines.
"""
```


## Django Best Practices

### Architecture

- Follow Django's established project and application conventions.
- Keep views focused on HTTP request and response handling.
- Put complex business logic in appropriate service or domain modules.
- Keep model methods focused on model-related behavior.
- Use custom managers and QuerySets for reusable database queries.
- Avoid putting substantial business logic in model `save()` methods.
- Avoid unnecessary signals.
- Prefer explicit dependencies over hidden application coupling.
- Keep applications loosely coupled.

### Models and Database

- Use Django's ORM whenever practical.
- Define explicit model relationships and appropriate database constraints.
- Use meaningful `related_name` values.
- Add database indexes when justified by query patterns.
- Avoid N+1 queries using `select_related()` and `prefetch_related()`.
- Use transactions for operations that must be atomic.
- Use `DecimalField` rather than floating-point fields for exact decimal
  values.
- Define appropriate `on_delete` behavior for relationships.
- Generate migrations whenever model definitions change.
- Review generated migrations before committing them.
- Never modify migrations that have already been applied in shared
  environments.
- Avoid raw SQL unless there is a demonstrated need.

### Django Settings

- Keep environment-specific configuration out of source code.
- Read secrets and sensitive configuration from environment variables.
- Never commit passwords, API keys, tokens, or credentials.
- Keep `DEBUG = False` in production.
- Configure `ALLOWED_HOSTS` appropriately.
- Separate development, testing, and production configuration where
  appropriate.
- Avoid hardcoding environment-specific URLs, paths, and credentials.

### Security

- Use Django's built-in authentication and authorization facilities.
- Apply CSRF protection where applicable.
- Validate all user-supplied input.
- Use Django's ORM to avoid SQL injection.
- Never disable security middleware without a documented reason.
- Avoid unsafe use of `mark_safe`, `eval`, and `exec`.
- Protect sensitive data in logs and API responses.
- Apply appropriate permissions to all protected functionality.

## Django REST Framework

Use Django REST Framework (DRF) for all API endpoints.

### API Architecture

- Use serializers for request validation and response serialization.
- Use DRF views, APIView, or ViewSets as appropriate.
- Prefer ModelViewSet or ReadOnlyModelViewSet when appropriate.
- Use routers for registering ViewSets.
- Keep views thin and move complex business logic into appropriate service
  modules.
- Use explicit serializers rather than exposing model fields indiscriminately.
- Define permissions explicitly.
- Use authentication classes appropriate to the application.
- Apply pagination to collection endpoints.
- Use filtering and ordering consistently.
- Follow REST conventions for HTTP methods and status codes.

### Serializers

- Validate all incoming data through serializers.
- Use explicit field definitions where appropriate.
- Implement custom validation in serializer validation methods.
- Avoid putting substantial business logic in serializers.
- Use read-only fields for values that clients must not modify.
- Avoid exposing sensitive model attributes.

### API Security

- Never assume that authentication alone provides authorization.
- Apply object-level permissions when necessary.
- Validate ownership and access rights before modifying resources.
- Avoid exposing internal database identifiers or sensitive information
  unnecessarily.
- Use appropriate throttling for endpoints that require it.
- Return consistent and meaningful API error responses.

### API Testing

- Use DRF's APIClient or APITestCase for API tests.
- Test successful and unsuccessful requests.
- Test authentication and permission enforcement.
- Test input validation.
- Test HTTP status codes and response structures.
- Test object-level authorization.
- Test pagination, filtering, and ordering where implemented.

## Dependency Management and Packaging

Use pip for dependency installation and management.

Use `pyproject.toml` as the primary project configuration and packaging file.

Use setuptools as the build backend.

Do not introduce alternative dependency managers such as Poetry, Pipenv, or uv.

### pyproject.toml

- Use PEP 621 project metadata.
- Configure setuptools through `pyproject.toml`.
- Configure package discovery to use `src/`.
- Declare runtime dependencies in the `[project]` section.
- Declare development dependencies using optional dependency groups.
- Keep tool configuration in `pyproject.toml` where supported.
- Avoid `setup.py` and `setup.cfg` unless required for compatibility with a
  specific tool or feature.

Example configuration:

```toml
[build-system]
requires = [
    'setuptools>=68',
]
build-backend = 'setuptools.build_meta'

[project]
name = 'django-media-tracker'
version = '0.1.0'
description = 'A Django application for tracking media collections'
requires-python = '>=3.11'
dependencies = [
    'Django>=5.2,<6.0',
    'djangorestframework>=3.16,<4.0',
]

[project.optional-dependencies]
dev = [
    'pytest',
    'pytest-django',
    'coverage',
    'ruff',
    'mypy',
]

[tool.setuptools.package-dir]
'' = 'src'

[tool.setuptools.packages.find]
where = [
    'src',
]
include = [
    'django_media_tracker*',
]
```

Adjust dependency versions to the project's actual supported Python and Django
versions.

### pip Usage

- Use a virtual environment for development.
- Never install project dependencies globally.
- Use pip to install, update, and uninstall dependencies.
- Keep runtime and development dependencies logically separated.
- Avoid unnecessary dependencies.
- Review dependency changes before introducing them.

The root Makefile must provide `make venv` to create `./.venv` if needed
and `make venv.install` to install `requirements-dev.txt` into it. Set
`PYTHON` in the Makefile to the virtual environment's interpreter and use
`$(PYTHON)` in every recipe that runs Python or Python-based tools. The
`venv` recipe uses a bootstrap interpreter to create the environment.

If requirements files are used, maintain them consistently with the
dependencies declared in `pyproject.toml`.

### Packaging

- Use setuptools for building distributions.
- Ensure package discovery is restricted to the `src/` layout.
- Do not include tests or unrelated files in runtime distributions unless
  explicitly required.
- Include necessary package data when applicable.
- Verify that builds produce valid wheels and source distributions.

## Testing Strategy

- Use Django's testing framework or pytest with pytest-django.
- Place tests alongside the code they exercise.
- Use descriptive test names that explain the expected behavior.
- Test both successful and unsuccessful execution paths.
- Test business logic independently where practical.
- Test model validation and database constraints.
- Test authentication and authorization.
- Avoid tests that depend on external services.
- Use mocks or fakes to isolate external dependencies.
- Do not introduce unnecessary test fixtures or complex test infrastructure.

Run `make test` from the repository root for the full workflow. The root
`Makefile` must provide a phony `test` target that runs the following phony
targets in order.

1. `make test.format` applies the project's formatting conventions to the codebase.
2. `make test.lint` runs all configured lint checks.
3. `make test.python` runs all configured Python test suites.

Keep each target runnable on its own and update the corresponding target when
adding a formatter, linter, or Python test suite.

## Code Quality and Formatting

Use Ruff for linting and formatting.

Configure Ruff in `pyproject.toml`.

- Follow PEP 8.
- Enforce the project's single-quote convention where supported.
- Use double quotes for f-strings and interpolated strings.
- Remove unused imports and variables.
- Avoid suppressing linting rules without justification.
- Use type checking where practical.
- Maintain meaningful test coverage.

Run lint checks with `make test.lint` and apply formatting with
`make test.format`.

Ensure the formatter configuration preserves the project's quoting conventions.

Note that Ruff's formatter cannot enforce different quote styles based on
whether a string is interpolated. Review f-strings and other interpolated
strings to ensure they use double quotes.

## Logging

- Use Python's standard `logging` module.
- Configure logging through Django settings.
- Never use `print()` for application logging.
- Include useful contextual information in log messages.
- Never log passwords, authentication tokens, or other sensitive information.

## Git and Repository Hygiene

- Use the `.markdown` extension for Markdown files, such as
  `README.markdown`. Keep a different extension when a specification
  requires it, as with `AGENTS.md`.
- Update references when renaming Markdown files, including paths in
  packaging metadata.

- Keep changes focused and logically organized.
- Avoid unrelated refactoring.
- Do not commit generated files, caches, virtual environments, or secrets.
- Review changes for accidental debugging statements and credentials.
- Keep documentation synchronized with application behavior.

### .gitignore Protection — Critical

The `.gitignore` file defines files and directories that must be treated as
inaccessible.

**Never read or write ignored files outside the exception below.**

The repository-root `.venv` may be created, updated, and used for project
development commands and dependency installation.

This prohibition includes:

- Reading their contents.
- Modifying or overwriting them.
- Creating files at ignored paths.
- Deleting or renaming them.
- Searching or scanning their contents.
- Using them as input to scripts or tools.
- Including their contents in generated reports or summaries.

Before accessing an existing file or directory:

1. Check whether its path is excluded by `.gitignore`.
2. If it is excluded, access it only if the `.venv` exception applies.
3. Do not attempt to circumvent ignore rules using alternative commands,
scripts, or tools.
4. If a requested task requires accessing an ignored file, stop and explain the
conflict.

Treat nested `.gitignore` files and applicable ignore patterns as
authoritative.

Do not use commands that recursively inspect the entire repository without
respecting ignore rules.

When listing files, prefer commands that honor Git ignore rules, such as:

```bash
git ls-files
```

For untracked files, use:

```bash
git ls-files --others --exclude-standard
```

Do not use `git clean` or other destructive cleanup commands.

## AI Agent Workflow

When working on this project:

1. Read this `AGENTS.md` before making changes.
2. Inspect the repository structure while respecting `.gitignore`.
3. Read relevant source files and tests before modifying them.
4. Keep all Python code under `src/`.
5. Place all Django applications under `src/django_media_tracker/apps/`.
6. Place tests alongside the code they test.
7. Follow the established Python and Django conventions.
8. Use Django REST Framework for API functionality.
9. Use pip and setuptools for dependency management and packaging.
10. Update or create tests for behavioral changes.
11. Generate and review migrations when modifying models.
12. Update documentation when changing application behavior or configuration.
13. Run relevant tests and quality checks after making changes.
14. Follow the ignored-file protection and its `.venv` exception.
15. Report any tests or checks that could not be executed.

When implementing a feature, prefer the smallest maintainable change that
satisfies the requirements.

When requirements are ambiguous, inspect existing conventions and choose the
implementation most consistent with the project architecture.

Do not introduce new frameworks, dependencies, architectural patterns, or
abstractions without a clear justification.
