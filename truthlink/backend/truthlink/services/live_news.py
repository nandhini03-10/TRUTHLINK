import re
import requests
from typing import List, Tuple
from xml.etree import ElementTree as ET

LIVE_NEWS_FEEDS = [
    "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
    "https://www.ndtv.com/rss",
    "https://www.news18.com/rss",
    "https://www.hindustantimes.com/rss/topnews/rssfeed.xml",
    "https://feeds.bbci.co.uk/news/rss.xml",
    "https://rss.cnn.com/rss/edition.rss",
    "https://www.aljazeera.com/xml/rss/all.xml",
    "https://www.reuters.com/world/rss.xml",
]

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"


def _fetch_feed(url: str) -> str:
    try:
        response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=10)
        response.raise_for_status()
        return response.text
    except Exception:
        return ""


def _parse_feed(content: str) -> List[Tuple[str, str, str]]:
    items: List[Tuple[str, str, str]] = []
    if not content:
        return items

    try:
        root = ET.fromstring(content)
    except ET.ParseError:
        return items

    # Support RSS and Atom formats
    for element in root.findall('.//item') + root.findall('.//entry'):
        title = element.findtext('title') or ''
        link = element.findtext('link') or ''
        if not link:
            href = element.find('link')
            if href is not None:
                link = href.get('href', '')
        description = element.findtext('description') or element.findtext('summary') or ''
        items.append((title.strip(), link.strip(), description.strip()))
    return items


def _query_matches(text: str, query: str) -> bool:
    query_lower = query.lower()
    text_lower = text.lower()
    if query_lower in text_lower:
        return True
    tokens = [token for token in re.findall(r"[A-Za-z0-9']+", query_lower) if len(token) >= 4]
    if not tokens:
        return False
    matches = sum(1 for token in set(tokens) if token in text_lower)
    return matches >= max(1, len(tokens) // 2)


def fetch_live_news(query: str, max_items: int = 6) -> List[Tuple[str, str]]:
    seen: set[str] = set()
    results: List[Tuple[str, str]] = []
    for feed_url in LIVE_NEWS_FEEDS:
        raw = _fetch_feed(feed_url)
        for title, link, description in _parse_feed(raw):
            if not link or link in seen:
                continue
            if _query_matches(f"{title} {description}", query):
                seen.add(link)
                results.append((link, title or link))
                if len(results) >= max_items:
                    return results
    return results
