# CLAUDE.md

## Project Overview

mathefragen.de — German math Q&A platform by Daniel Jung Media GmbH.
Built with Django, Python 3.12, PostgreSQL. Deployed via Docker Swarm + GitLab CI/CD.

Live: https://mathefragen.de

## Tech Stack

- **Framework:** Django 5.x, Django REST Framework
- **Language:** Python 3.12
- **Database:** PostgreSQL (SQLite for tests)
- **Auth:** JWT (simplejwt) + Session
- **Storage:** AWS S3 (django-storages + boto3), Cloudflare CDN
- **Sessions:** Redis Sentinel (production), default (development)
- **Email:** SendGrid SMTP
- **Bot Protection:** Cloudflare Turnstile
- **Notifications:** Firebase Cloud Messaging (pyfcm)
- **Dependency Management:** Poetry

## Development Setup

### Docker (recommended)
```sh
docker compose up
docker compose exec django python manage.py createsuperuser
```

### Poetry (local)
```sh
poetry install
docker compose up -d postgres
poetry run python manage.py migrate
poetry run python manage.py runserver
```

### First-time setup
```sh
python manage.py compress  # Required for django-compressor
```

## Testing
```sh
python manage.py test
# Uses SQLite automatically (see settings/__init__.py)
```

## Project Structure

```
mathefragen/
  settings/__init__.py   # All Django settings
  urls.py                # Root URL configuration
  apps/                  # All Django apps (see below)
  templates/             # Django templates (base.html is the main layout)
  site-static/           # CSS, JS, images, fonts
  lib.py                 # Turnstile validation utility
custom_storages.py       # S3 storage backends
docker-compose.yml       # Dev environment (Django + PostgreSQL)
Dockerfile               # Multi-stage production build
pyproject.toml           # Dependencies (Poetry)
gunicorn.conf.py         # Production server config
```

## Key Django Apps

| App | Purpose |
|-----|---------|
| `core` | Base models (hash_id, idate, udate), middleware, context processors, utilities |
| `question` | Questions, answers, comments — the central domain |
| `user` | User profiles, auth, registration, badges, certificates |
| `hashtag` | Tag system for questions |
| `vote` | Upvote/downvote on questions, answers, comments |
| `search` | Search functionality |
| `tutoring` | Paid tutoring sessions (PayPal integration) |
| `guardian` | IP blocking, spam protection, content reporting |
| `playlist` | Learning playlists |
| `news` | Articles and release notes |
| `settings` | Admin-configurable site settings (Global, HeaderMenu, Footer, SEO, etc.) |
| `notifier` | Firebase push notifications |
| `review` | User skill verification reviews |
| `stats` | Global statistics |
| `aiedn` | AI integration endpoint |
| `messaging` | In-app messaging/notifications |
| `follow` | Follow users, questions, hashtags |
| `promotion` | Promotional banners |
| `tips` | Tips and suggestion banners |
| `video` | Video/playlist categories |
| `feedback` | User feedback |

## API

REST API at `/v1/` with JWT authentication. Documentation at `/api/schema/swagger-ui/`.

Key endpoints: `/v1/user/`, `/v1/question/`, `/v1/vote/`, `/v1/search/`, `/v1/hashtag/`, `/v1/review/`, `/v1/stats/`

## Coding Conventions

- Function-based views for simple endpoints; class-based views for forms
- DRF `@api_view` decorators for API endpoints
- `Base` model mixin (in `core/models.py`) provides `hash_id`, `idate`, `udate` to all models
- Profile created via `post_save` signal on User model
- Templates use `{% load custom_tags %}` for custom template tags
- Markdown rendering via `django-markdownify` (`|markdownify` filter)
- MathJax for math formula rendering in templates
- German language (`LANGUAGE_CODE = 'de'`, `TIME_ZONE = 'Europe/Berlin'`)

## Deployment

- GitLab CI/CD builds Docker image on semantic version tags
- Tag format: `MajorRelease.MinorRelease.HotFixes` (e.g., `1.2.25`)
- Production: Docker Swarm with gunicorn
- Env files on production server: `/var/www/aiedn/apps/mathefragen.de/`
- Admin URL: configured via `ADMIN_URL` setting (not at `/admin/`)

## Environment Variables

See `.env.example` for all required variables. Key ones:
- `SECRET_KEY`, `DEBUG`, `DOMAIN`, `ALLOWED_HOSTS`
- `DB_NAME`, `DB_USER`, `DB_PWD`, `DB_HOST`, `DB_PORT`
- `AWS_STORAGE_BUCKET_NAME`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`
- `SENDGRID_KEY`, `TURNSTILE_SITE_KEY`, `TURNSTILE_SECRET_KEY`
- `FIREBASE_SERVER_KEY`
