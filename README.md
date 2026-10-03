# Django2025: Content and Account Coursework

**A Django learning project covering content pages, account flows, and comments.** The comment-path repair adds regression tests for form handling, ownership, request methods, and CSRF protection. This remains a local educational project.

**Review guide:** [request flow, migration boundaries, and verification record](docs/REVIEW_GUIDE.md).

**Start here:** [`product/models.py`](product/models.py), [`product/views.py`](product/views.py), and [`product/tests.py`](product/tests.py).

## Learning goals and contribution record

The project practices the connection between Django models, forms, view functions, routes, and server-rendered templates. The public history records the [initial repository](https://github.com/JAEUK02/Django2025/commit/736ca0a1202ea3c1219a460774e566e892b70ee1) and [weekly coursework snapshot](https://github.com/JAEUK02/Django2025/commit/7b8b8a228eefedbf07ec7d2bfea4cca8531b8476). The current repair builds on that coursework; the original implementation and later maintenance work can be distinguished in the commit history.

## Implemented code paths

- `MainContent` defines a title, body, and publication date; list/detail views render those records.
- Account routes use Django's login/logout views and a custom signup flow based on `UserCreationForm`.
- Comments belong to a user and a content record. Create/update forms edit only the comment body; the view sets or preserves ownership.
- Comment editing supports GET and POST, with invalid bound forms and errors preserved.
- Deletion requires an authenticated owner, a POST request, and a CSRF token.
- Tests cover these comment paths and body rendering, including denied requests that must leave stored data unchanged.

**Stack:** Python, Django, SQLite, HTML templates, and Bootstrap CSS. The settings were originally generated with Django 5.1.1. The repair was tested with Django 5.2.17 and, as a historical compatibility check, Django 5.1.1.

## Repository map

| Path | Purpose |
| --- | --- |
| `my_project/` | Settings and root routing |
| `accounts/` | Signup form/view and authentication routes |
| `product/` | Content/comment models, forms, views, routes, and regression tests |
| `product/migrations/` | Tracked initial schema for fresh databases |
| `pages/` | Static page views |
| `templates/` | Shared layout and rendered pages |
| `static/` | Local CSS assets |

## Fresh local setup

**The following steps are for a fresh disposable checkout/database. If you already have a database or locally generated migrations, stop and review the [existing-database warning](docs/REVIEW_GUIDE.md#existing-databases-need-a-separate-plan) first. The initial migration is not an automatic upgrade path.**

The verified environment used Python 3.12.14. Use synthetic data and bind any development server to localhost:

```bash
git clone https://github.com/JAEUK02/Django2025.git
cd Django2025
python3 -m venv .venv
source .venv/bin/activate
python -m pip install "Django==5.2.17" "asgiref==3.12.1" "sqlparse==0.6.0"
python manage.py check
python manage.py migrate
python manage.py test
python manage.py createsuperuser
python manage.py runserver 127.0.0.1:8000
```

On Windows, activate with `.venv\Scripts\activate`. A fresh install uses the committed migration and does not need `makemigrations`. Create sample content in `/admin/`, then inspect it in `/product/`.

## Verification and limits

The full available suite contains **27 tests**, passing on Python 3.12.14 with Django 5.2.17 and 5.1.1. The tests cover comment ownership, anonymous access, bound form errors, forged author/parent inputs, HTTP-method rejection, CSRF enforcement, escaping, and related admin search.

Fresh SQLite migration, a repeat migration with nothing left to apply, model/migration drift checks, system checks, and source compilation passed in disposable environments. See the [verification record](docs/REVIEW_GUIDE.md#repair-verification) for the boundaries.

- Existing databases and local migration histories were not inspected or upgraded.
- Browser layout, complete signup/login journeys, deployment, and production security were not validated by this repair.
- The settings are development-only. Passing these tests does not make them deployment-ready.
- Dependency versions are recorded above, but the repository still has no dependency lock or CI workflow.
