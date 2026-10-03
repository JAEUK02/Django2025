# Django2025: Content and Account Coursework

**A Django learning project covering content pages, account flows, and comment-related views.** It records an early web-development exercise and has known issues in the comment implementation.

**Review guide:** [request flow, route map, and verified local checks](docs/REVIEW_GUIDE.md).

**Start here:** [`product/models.py`](product/models.py), [`product/views.py`](product/views.py), and [`accounts/views.py`](accounts/views.py).

## Learning goals and contribution record

The project practices the connection between Django models, forms, view functions, routes, and server-rendered templates. The public history records the [initial repository](https://github.com/JAEUK02/Django2025/commit/736ca0a1202ea3c1219a460774e566e892b70ee1) and subsequent weekly-development commits, including [the application-code snapshot](https://github.com/JAEUK02/Django2025/commit/7b8b8a228eefedbf07ec7d2bfea4cca8531b8476).

## Implemented code paths

- `MainContent` defines a title, body, and publication date; list/detail views render those records.
- Account routes use Django's login/logout views and a custom signup flow based on `UserCreationForm`.
- Comment create/update/delete views demonstrate authentication decorators and ownership checks in the source. Known model/import problems mean these flows need correction before being treated as working features.
- Templates provide a shared page structure, navigation, account forms, and content/comment pages.

**Stack:** Python, Django, SQLite, HTML templates, and Bootstrap CSS. The settings file was generated with Django 5.1.1; the repository does not lock the runtime dependency versions.

## Repository map

| Path | Purpose |
| --- | --- |
| `my_project/` | Settings and root routing |
| `accounts/` | Signup form/view and authentication routes |
| `product/` | Content and comment models, forms, views, and routes |
| `pages/` | Static page views |
| `templates/` | Shared layout and rendered pages |
| `static/` | Local CSS assets |

## Local exploration

Use a fresh checkout and a compatible Django/Python environment. The repository does not include a requirements file or committed product migrations.

```bash
git clone https://github.com/JAEUK02/Django2025.git
cd Django2025
python3 -m venv .venv
source .venv/bin/activate
# Historical local diagnostic environment; see docs/REVIEW_GUIDE.md
python -m pip install "Django==5.1.1" "asgiref==3.12.1" "sqlparse==0.6.0"
python manage.py check
python manage.py makemigrations product
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Use synthetic data and localhost only. These commands create a local development database. Source compilation, Django checks, fresh database migration, and selected test-client requests were verified on Python 3.12.14 / Django 5.1.1; no browser or end-to-end account flow was tested. See the [verification record](docs/REVIEW_GUIDE.md#what-was-actually-verified) for the exact scope and failures.

## Status and known limits

This is a coursework snapshot rather than a maintained deployed application.

- `Comment.author` currently references the `Comment` model itself, while the create view assigns `request.user`.
- Update/delete views refer to `Comment` without importing it.
- The update view's GET path has no response, and an invalid POST recreates the form without retaining its validation errors.
- The detail template has an unclosed content expression, so the body does not render correctly.
- The test command discovers 0 tests; the scaffold files do not establish coverage of the account or comment flows.

These issues are recorded for a future code review. This documentation change preserves the existing application source.
