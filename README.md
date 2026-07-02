# NEXUS ATHLETE (SmartFootballCompanion)

A football companion app: log match stats and get trend-based AI insights, run a live match tracker, browse league tables/fixtures/results, read daily football news, watch curated training drills, and manage a player card.

## Stack
- Flask (app factory + blueprints in `app/`)
- Flask-SQLAlchemy + Flask-Migrate (models in `app/models.py`)
- Flask-Login (session auth) + Flask-WTF (CSRF)
- Shared design system: `templates/base.html` + `static/app.css` (clean, card-based UI; every page extends `base.html`)
- `app/services/analytics.py` — trend-based performance insights (rolling stats + linear trend slopes via numpy, not a hardcoded formula)
- `app/services/football_news.py` — daily headlines + transfer news via BBC Sport RSS feeds (free, no API key)
- `app/services/football_data.py` — league tables/fixtures/results via [TheSportsDB](https://www.thesportsdb.com)'s free tier (curated set of ~10 major leagues; no true live scores on the free plan, only fixtures/results/standings, cached ~10 min in-process to respect the shared test key's rate limits)
- `app/drills_data.py` — curated real YouTube training-drill videos per skill, standard iframe embeds
- Player avatars via [DiceBear](https://www.dicebear.com) (generated, no rights issues — no real player photos used)

## Setup
```bash
pip install -r requirements.txt
cp .env.example .env   # edit SECRET_KEY for anything beyond local dev
flask db upgrade        # creates/updates nexus.db from migrations/
```

## Run
```bash
python wsgi.py           # dev server
# or
gunicorn wsgi:app        # production (matches Procfile)
```

## Test
```bash
pytest
```

## Project layout
```
app/
  __init__.py       create_app() factory (also self-heals the schema via db.create_all() on startup)
  config.py         env-based config (SECRET_KEY, DATABASE_URL, FLASK_DEBUG) - DB defaults to a local-appdata path, not the repo folder, to avoid cloud-sync file locking
  extensions.py     db, migrate, login_manager, csrf singletons
  models.py         User, StatEntry, Match, MatchEvent
  auth.py           /login /register /logout
  main.py           / /dashboard /health /live* /news /leagues* /drills /profile
  drills_data.py    curated training-drill video list
  services/
    analytics.py      PerformanceAnalyzer
    football_news.py  BBC Sport RSS (headlines + transfers)
    football_data.py  TheSportsDB client (leagues/table/fixtures/results) + TTL cache
templates/          Jinja templates - base.html + per-page content blocks
static/app.css      shared design system stylesheet
tests/              pytest suite
migrations/          Alembic migration history
```

## Environment variables
See `.env.example`. `SECRET_KEY` must be a real secret outside local dev — sessions and CSRF tokens are signed with it. `DATABASE_URL` defaults to a local per-user app-data SQLite file if unset (deliberately outside the repo folder — see `app/config.py`).

## Deploying
The repo is deploy-ready (env-based config, `Procfile` targeting `wsgi:app`) for any Python host (Render, Railway, Fly, etc.). Set `SECRET_KEY` and `DATABASE_URL` in the host's environment/dashboard, then run `flask db upgrade` once against the production database before first boot.

## Known scope cuts (deliberate, not oversights)
- No Strava/device import — would need a registered OAuth developer app; flagged as a future phase.
- No true live league scores — TheSportsDB's free tier only has fixtures/results/standings, not minute-by-minute live data. A paid provider (e.g. football-data.org with an API key) would be needed for that.
- League coverage is a curated ~10 major leagues, not every league worldwide.
- No PWA, no light/dark toggle, no websockets — kept out of scope for this size of project.
- Analytics is statistical trend detection (rolling averages, linear regression slopes, z-score outliers), not a trained ML model — appropriate for a single user's own history rather than a large training set.
- AI Coach is presented as an animated chat assistant but is backed by the same statistical engine above, not a real LLM — the message format (`ai_messages`) is structured so a real chat backend could replace it later.
