# Source walkthrough and verification

This guide follows the comment-path repair built on [the reviewed baseline](https://github.com/JAEUK02/Django2025/tree/3d999636873441e9406611ef3501aa934b9dad5a). It separates the application flow, fresh-install schema, and verified regression coverage from work that remains untested.

## Read one request end to end

For the content detail page, follow:

1. [Root routes](../my_project/urls.py) send `/product/` requests to the product app.
2. [Product routes](../product/urls.py) capture `content_id` and call `detail`.
3. [The view](../product/views.py) uses `get_object_or_404(MainContent, pk=content_id)`.
4. [The model](../product/models.py) defines the title, content, and publication date.
5. [The template](../templates/product/content_detail.html) receives that object as `content_list` and iterates its reverse `comment_set` relation.

For signup, [`accounts/urls.py`](../accounts/urls.py) selects [`signup`](../accounts/views.py), which validates [`SignupForm`](../accounts/forms.py), saves a user, logs them in, and redirects to `/`. Login and logout use Django's built-in auth views.

This is a server-rendered Django application: view functions assemble template context, and SQLite stores records. There is no separate API/frontend service in this repository.

## Route map

| URL | Source entry point | What to inspect |
| --- | --- | --- |
| `/`, `/company/` | `pages/urls.py` → `pages/views.py` | Static template rendering |
| `/product/` | `product.views.index` | Publication-date ordering |
| `/product/<id>/` | `product.views.detail` | Object lookup and related comments |
| `/accounts/signup/` | `accounts.views.signup` | Form validation and login after signup |
| `/accounts/login/` | `LoginView` | Built-in authentication with a custom template |
| `/accounts/logout/` | `LogoutView` | POST form in the navbar |
| `/product/comment/create/<id>/` | `comment_create` | Login requirement, form, and relationship assignment |
| `/product/comment/update/<id>/` | `comment_update` | Owner-only GET edit form and POST validation |
| `/product/comment/delete/<id>/` | `comment_delete` | Owner-only POST deletion with CSRF protection |
| `/admin/` | Django admin | `MainContent` and `Comment` registration |

Create and update accept GET/POST; delete accepts POST only. Login is required for all three. The form exposes only `content`, while the view binds or preserves the author and parent record.

## Fresh database and migration contract

The tracked [initial product migration](../product/migrations/0001_initial.py) creates `MainContent` and `Comment`. `Comment.author` points to `settings.AUTH_USER_MODEL`, and the migration declares `migrations.swappable_dependency(settings.AUTH_USER_MODEL)`.

The local `accounts` and `pages` apps define no database models, so they need no initial schema migration. Django's built-in auth, admin, contenttypes, and session migrations are supplied by Django. The previous blanket `migrations/` ignore rule has been removed so the product migration is versioned.

For a **new disposable checkout with no existing database**, follow the environment setup in the README, then:

```bash
python manage.py check
python manage.py migrate
python manage.py showmigrations product
python manage.py makemigrations --check --dry-run
python manage.py test
```

`showmigrations product` should show `[X] 0001_initial`. The drift check should report no changes. A second `migrate` should report no migrations to apply. The checked-in migration supplies the initial schema; do not generate a different local initial migration as part of a fresh install.

### Existing databases need a separate plan

An existing development database may have the old self-referencing `Comment.author` foreign key and locally generated migrations that were never committed. It may already record a migration named `product.0001_initial`. Reusing that name does not cause Django to rewrite the old schema.

Before any upgrade, a maintainer must separately inspect the actual schema, recorded migration history, local migration files, and existing ownership data, with a recoverable backup. Numeric values that referenced comments cannot safely be reinterpreted as user IDs.

This repair does **not** supply an existing-database conversion or authorize a reset. Do not delete a database or migration history, or use `--fake` / `--fake-initial` as a shortcut. Django's initial-migration detection does not establish that an existing self-FK is compatible with the new user FK. See the [official migration guidance](https://docs.djangoproject.com/en/5.2/topics/migrations/#initial-migrations).

## Repair verification

Verified on 2026-10-03 in isolated Python 3.12.14 environments:

| Check | Django 5.2.17 | Django 5.1.1 historical compatibility |
| --- | --- | --- |
| Full available test suite | 27 passed | 27 passed |
| Fresh SQLite migration using the tracked initial migration | Passed | Passed |
| Repeat migration | No migrations to apply | No migrations to apply |
| `makemigrations --check --dry-run` | No changes detected | No changes detected |
| Synthetic user/content/comment creation in the migrated schema | Passed | Passed |

The fresh-schema check also inspected the actual SQLite foreign keys: `author_id` references `auth_user.id`, and `content_list_id` references `product_maincontent.id`. The product initial migration was recorded as applied.

Django system checks, Python source compilation, and `git diff --check` also passed. Both environments used `asgiref==3.12.1` and `sqlparse==0.6.0`. Django 5.1.1 was used only to compare against the original coursework environment; it is an unsupported historical version. The README's local setup uses the tested 5.2 LTS release; see [Django's support table](https://www.djangoproject.com/download/#supported-versions).

Tests run against temporary test databases; the independent migration checks used newly created disposable SQLite files and synthetic records. The local audit used a placeholder development key. No existing user database was read or migrated.

### What the tests exercise

[`product/tests.py`](../product/tests.py) covers:

- Actual body rendering and automatic escaping of body/comment text, including text that could otherwise escape a textarea.
- Valid create/update operations, correct redirects, and rejection of forged author or parent inputs.
- Edit-form GET responses and invalid empty/whitespace submissions that retain bound data and visible errors.
- Owner, non-owner, and anonymous requests, with stored records checked after denied actions.
- GET/HEAD/unsupported-method deletion attempts that return 405 without deleting anything.
- Valid owner POST deletion that removes only the selected comment.
- Create, update, and delete requests with `Client(enforce_csrf_checks=True)`: missing tokens return 403 without mutation; tokens obtained from rendered forms permit valid requests.
- An owner-only delete POST form with its own CSRF input, no nested forms, and no destructive delete link.
- Comment admin search through the related author's username.

Three focused tests were run against the pre-repair source and failed on the reproduced author assignment, missing `Comment` import, and missing body interpolation. The repaired full suite passes.

## Scope and remaining limits

The repair addresses the demonstrated comment-path defects: author relation/import, update GET and bound errors, body interpolation and malformed form markup, POST-only deletion, and the associated admin author lookup.

This is still coursework, with a bounded regression suite:

- No existing-database upgrade was attempted or verified.
- Account signup/login journeys, visual browser layout, broader application coverage, accessibility, and deployment were not validated by this repair.
- Development settings remain unsuitable for production.
- There is no CI workflow or dependency lock in this repository. A local green suite is not a remote CI result.
