import time

import requests

BASE_URL = "https://www.thesportsdb.com/api/v1/json/3"
CACHE_TTL_SECONDS = 600

# Curated set of major leagues available on TheSportsDB's free tier.
# Not "every league" - the free test key only reliably covers these.
LEAGUES = [
    {"id": "4328", "name": "English Premier League", "country": "England"},
    {"id": "4329", "name": "English League Championship", "country": "England"},
    {"id": "4330", "name": "Scottish Premiership", "country": "Scotland"},
    {"id": "4331", "name": "German Bundesliga", "country": "Germany"},
    {"id": "4332", "name": "Italian Serie A", "country": "Italy"},
    {"id": "4334", "name": "French Ligue 1", "country": "France"},
    {"id": "4335", "name": "Spanish La Liga", "country": "Spain"},
    {"id": "4336", "name": "Greek Super League 1", "country": "Greece"},
    {"id": "4337", "name": "Dutch Eredivisie", "country": "Netherlands"},
    {"id": "4338", "name": "Belgian Pro League", "country": "Belgium"},
]

_cache = {}


def _cached_get(url, timeout=5):
    now = time.time()
    cached = _cache.get(url)
    if cached and now - cached[0] < CACHE_TTL_SECONDS:
        return cached[1]

    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
    except (requests.RequestException, ValueError):
        return cached[1] if cached else None

    _cache[url] = (now, data)
    return data


def get_leagues():
    """Curated list of major leagues (not the full global catalog)."""
    return LEAGUES


def get_league_by_id(league_id):
    return next((league for league in LEAGUES if league["id"] == league_id), None)


def get_table(league_id, season="2025-2026"):
    data = _cached_get(f"{BASE_URL}/lookuptable.php?l={league_id}&s={season}")
    return (data or {}).get("table") or []


def get_fixtures(league_id):
    data = _cached_get(f"{BASE_URL}/eventsnextleague.php?id={league_id}")
    return (data or {}).get("events") or []


def get_results(league_id):
    data = _cached_get(f"{BASE_URL}/eventspastleague.php?id={league_id}")
    return (data or {}).get("events") or []
