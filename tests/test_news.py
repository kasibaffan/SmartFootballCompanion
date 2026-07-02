import app.services.football_news as football_news_module

FEED_XML = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:media="http://search.yahoo.com/mrss/">
  <channel>
    <item>
      <title><![CDATA[Player A joins Club B]]></title>
      <link>https://example.com/1</link>
      <description><![CDATA[A big money move.]]></description>
      <pubDate>Wed, 01 Jul 2026 12:00:00 GMT</pubDate>
      <media:thumbnail width="240" height="135" url="https://example.com/1.jpg"/>
    </item>
    <item>
      <title><![CDATA[Player C linked with Club D]]></title>
      <link>https://example.com/2</link>
      <description><![CDATA[Rumours swirl.]]></description>
      <pubDate>Wed, 01 Jul 2026 09:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>"""

SINGLE_ITEM_XML = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
  <item>
    <title><![CDATA[All done deals in July]]></title>
    <link>https://example.com/roundup</link>
    <description><![CDATA[Roundup.]]></description>
    <pubDate>Wed, 01 Jul 2026 19:00:00 GMT</pubDate>
  </item>
</channel></rss>"""


class FakeResponse:
    def __init__(self, content, status=200):
        self.content = content.encode("utf-8")
        self.status = status

    def raise_for_status(self):
        if self.status >= 400:
            raise football_news_module.requests.RequestException("boom")


def test_get_headlines_parses_multiple_items(monkeypatch):
    monkeypatch.setattr(football_news_module.requests, "get", lambda url, timeout=None: FakeResponse(FEED_XML))
    items = football_news_module.get_headlines()
    assert len(items) == 2
    assert items[0]["title"] == "Player A joins Club B"
    assert items[0]["thumbnail"] == "https://example.com/1.jpg"
    assert items[1]["thumbnail"] is None


def test_get_transfer_news_handles_single_item_feed(monkeypatch):
    monkeypatch.setattr(football_news_module.requests, "get", lambda url, timeout=None: FakeResponse(SINGLE_ITEM_XML))
    items = football_news_module.get_transfer_news()
    assert len(items) == 1
    assert items[0]["title"] == "All done deals in July"


def test_feed_parsing_returns_empty_list_on_failure(monkeypatch):
    def raise_error(url, timeout=None):
        raise football_news_module.requests.RequestException("network down")

    monkeypatch.setattr(football_news_module.requests, "get", raise_error)
    assert football_news_module.get_headlines() == []
    assert football_news_module.get_transfer_news() == []


def test_feed_parsing_returns_empty_list_on_bad_xml(monkeypatch):
    monkeypatch.setattr(football_news_module.requests, "get", lambda url, timeout=None: FakeResponse("not xml"))
    assert football_news_module.get_headlines() == []


def test_news_route_renders_both_tabs(auth_client, monkeypatch):
    import app.main as main_module

    monkeypatch.setattr(main_module, "get_headlines", lambda: [
        {"title": "Test Headline", "link": "https://example.com", "description": "desc", "pub_date": "", "thumbnail": None}
    ])
    monkeypatch.setattr(main_module, "get_transfer_news", lambda: [])

    resp = auth_client.get("/news")
    assert resp.status_code == 200
    assert b"Test Headline" in resp.data
    assert b"No transfer news available" in resp.data
