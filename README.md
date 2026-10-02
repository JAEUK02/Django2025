# Django2025: Content and Account Coursework

**A Django learning project covering content pages, account flows, and comment-related views.** It records an early web-development exercise and has known issues in the comment implementation.

**Start here:** [`product/models.py`](product/models.py), [`product/views.py`](product/views.py), and [`accounts/views.py`](accounts/views.py).

## Learning goals and contribution record

The project practices the connection between Django models, forms, view functions, routes, and server-rendered templates. The public history records the [initial repository](https://github.com/JAEUK02/Django2025/commit/736ca0a1202ea3c1219a460774e566e892b70ee1) and subsequent weekly-development commits, including [the current public snapshot](https://github.com/JAEUK02/Django2025/commit/7b8b8a228eefedbf07ec7d2bfea4cca8531b8476).

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
python manage.py check
python manage.py makemigrations product
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

This creates a local development database. Content can be inspected through the development admin and list/detail pages. The commands describe the intended development workflow; a clean runtime has not been verified for this documentation review.

## Status and known limits

This is archived coursework rather than a maintained deployed application.

- `Comment.author` currently references the `Comment` model itself, while the create view assigns `request.user`.
- Update/delete views refer to `Comment` without importing it.
- The update view's GET path has no response, and an invalid POST recreates the form without retaining its validation errors.
- The test files are Django scaffolds; they do not establish coverage of the account or comment flows.

These issues are recorded for a future code review. This documentation change preserves the existing application source.
