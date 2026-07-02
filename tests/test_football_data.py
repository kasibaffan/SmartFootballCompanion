import app.services.football_data as football_data_module


class FakeResponse:
    def __init__(self, data, status=200):
        self._data = data
        self.status = status

    def raise_for_status(self):
        if self.status >= 400:
            raise football_data_module.requests.RequestException("boom")

    def json(self):
        return self._data


def setup_function():
    football_data_module._cache.clear()


def test_get_leagues_returns_curated_list():
    leagues = football_data_module.get_leagues()
    assert len(leagues) == 10
    assert any(l["name"] == "English Premier League" for l in leagues)


def test_get_league_by_id_found_and_not_found():
    assert football_data_module.get_league_by_id("4328")["name"] == "English Premier League"
    assert football_data_module.get_league_by_id("nonexistent") is None


def test_get_table_parses_standings(monkeypatch):
    monkeypatch.setattr(
        football_data_module.requests, "get",
        lambda url, timeout=None: FakeResponse({"table": [{"intRank": "1", "strTeam": "Arsenal"}]}),
    )
    table = football_data_module.get_table("4328")
    assert table == [{"intRank": "1", "strTeam": "Arsenal"}]


def test_get_fixtures_and_results_handle_missing_events_key(monkeypatch):
    monkeypatch.setattr(football_data_module.requests, "get", lambda url, timeout=None: FakeResponse({"events": None}))
    assert football_data_module.get_fixtures("4328") == []
    assert football_data_module.get_results("4328") == []


def test_requests_are_cached_within_ttl(monkeypatch):
    calls = []

    def fake_get(url, timeout=None):
        calls.append(url)
        return FakeResponse({"table": []})

    monkeypatch.setattr(football_data_module.requests, "get", fake_get)
    football_data_module.get_table("4328")
    football_data_module.get_table("4328")
    assert len(calls) == 1


def test_network_failure_returns_empty_not_exception(monkeypatch):
    def raise_error(url, timeout=None):
        raise football_data_module.requests.RequestException("network down")

    monkeypatch.setattr(football_data_module.requests, "get", raise_error)
    assert football_data_module.get_table("4328") == []
    assert football_data_module.get_fixtures("4328") == []


def test_leagues_route_lists_curated_leagues(auth_client):
    resp = auth_client.get("/leagues")
    assert resp.status_code == 200
    assert b"English Premier League" in resp.data


def test_league_detail_route_renders_tabs(auth_client, monkeypatch):
    import app.main as main_module

    monkeypatch.setattr(main_module, "get_table", lambda league_id: [{"intRank": "1", "strTeam": "Arsenal", "intPlayed": "10", "intWin": "8", "intDraw": "1", "intLoss": "1", "intGoalDifference": "20", "intPoints": "25"}])
    monkeypatch.setattr(main_module, "get_fixtures", lambda league_id: [])
    monkeypatch.setattr(main_module, "get_results", lambda league_id: [])

    resp = auth_client.get("/leagues/4328")
    assert resp.status_code == 200
    assert b"Arsenal" in resp.data


def test_league_detail_route_rejects_unknown_league(auth_client):
    resp = auth_client.get("/leagues/nonexistent", follow_redirects=True)
    assert resp.status_code == 200
    assert b"Unknown league" in resp.data
