import xml.etree.ElementTree as ET

import requests

HEADLINES_FEED_URL = "https://feeds.bbci.co.uk/sport/football/rss.xml"
TRANSFERS_FEED_URL = "https://feeds.bbci.co.uk/sport/football/transfers/rss.xml"
MEDIA_NS = "{http://search.yahoo.com/mrss/}"


def _parse_feed(url, timeout=5):
    """Returns a list of {'title','link','description','pub_date','thumbnail'} dicts
    parsed from an RSS feed, or [] if the feed is unavailable."""
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
    except (requests.RequestException, ET.ParseError):
        return []

    items = []
    for item in root.findall("./channel/item"):
        thumbnail = item.find(f"{MEDIA_NS}thumbnail")
        items.append(
            {
                "title": (item.findtext("title") or "").strip(),
                "link": (item.findtext("link") or "").strip(),
                "description": (item.findtext("description") or "").strip(),
                "pub_date": (item.findtext("pubDate") or "").strip(),
                "thumbnail": thumbnail.get("url") if thumbnail is not None else None,
            }
        )
    return items


def get_headlines(timeout=5):
    """Daily football headlines from BBC Sport's general football feed."""
    return _parse_feed(HEADLINES_FEED_URL, timeout=timeout)


def get_transfer_news(timeout=5):
    """Transfer-specific news from BBC Sport's football transfers feed."""
    return _parse_feed(TRANSFERS_FEED_URL, timeout=timeout)
