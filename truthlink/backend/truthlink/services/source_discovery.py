import requests
from bs4 import BeautifulSoup
from typing import List, Tuple, Dict, Set
from urllib.parse import urlparse, parse_qs, unquote
import re

from truthlink.services.ai_engine import compute_similarity
from truthlink.services.live_news import fetch_live_news

DEBUG = False

# High-authority domains for specific claim types
VERIFIED_CELEBRITY_SOURCES = {
    "twitter.com", "x.com", "instagram.com", "facebook.com",  # Official celebrity accounts
    "thehindu.com", "thenewsminute.com", "cinemaexpress.com", "behindwoods.com",  # Major Tamil entertainment news
    "deccanchronicle.com", "indianexpress.com", "theprint.in"  # Established news agencies
}

VERIFIED_POLITICAL_SOURCES = {
    "pib.gov.in",  # Press Information Bureau
    "tnscheme.gov.in", "tnssc.gov.in",  # Tamil Nadu government sources
    "eci.gov.in",  # Election Commission
    "thehindu.com", "deccanchronicle.com", "theprint.in",  # Major news outlets
    "thewire.in", "scroll.in"  # Established independent media
}

MAJOR_NEWS_SOURCES = {
    "thehindu.com", "deccanchronicle.com", "indianexpress.com", "theprint.in", "scroll.in", "thewire.in", "thenewsminute.com", "cinemaexpress.com",
    "ndtv.com", "news18.com", "timesofindia.indiatimes.com", "timesofindia.com", "indiatoday.in", "economictimes.indiatimes.com", "hindustantimes.com", "abplive.com", "republicworld.com", "zeenews.com",
    "bbc.co.uk", "bbc.com", "cnn.com", "aljazeera.com", "thequint.com", "newsroompost.com", "news9live.com", "telegraphindia.com",
    "aajtak.in", "firstpost.com", "livemint.com", "business-standard.com", "moneycontrol.com", "news24.com", "oneindia.com", "newsnationtv.com", "timesnownews.com",
    "industriever.com", "reuters.com", "apnews.com", "cnbc.com", "foxnews.com"
}

# Entertainment gossip sites (low authority for major claims)
GOSSIP_SOURCES = {
    "indianet", "vikatan.com", "maalai", "dinathanthi",  # Tamil entertainment blogs
    "youtube.com", "instagram.com/stories",  # Social media (unverified sources)
    "reddit.com", "quora.com",  # User discussions
}

TRUSTED_SOCIAL_DOMAINS = {
    "twitter.com", "x.com", "instagram.com", "facebook.com", "youtube.com"
}

TRUSTED_NEWS_DOMAINS = {
    "reuters.com", "apnews.com", "bbc.com", "bbc.co.uk", "cnn.com", "aljazeera.com",
    "ndtv.com", "news18.com", "thehindu.com", "indianexpress.com", "hindustantimes.com",
    "timesofindia.com", "telegraphindia.com", "theprint.in", "scroll.in", "thewire.in",
    "economictimes.indiatimes.com", "business-standard.com", "livemint.com", "cnbc.com"
}


def detect_claim_type(claim: str) -> str:
    """Detect if claim is about celebrity, political, business, or general."""
    claim_lower = claim.lower()
    
    # Celebrity keywords
    if any(word in claim_lower for word in ["messi", "marry", "married", "wedding", "affair", "relationship", "actor", "actress", "star", "hero", "heroine", "film", "movie", "cast", "co-star"]):
        return "celebrity"
    
    # Political keywords
    if any(word in claim_lower for word in ["resign", "minister", "cm", "chief minister", "mla", "mp", "election", "government", "policy", "law", "parliament", "assembly"]):
        return "political"
    
    # Business keywords
    if any(word in claim_lower for word in ["company", "startup", "ipo", "layoff", "shutdown", "merger", "acquisition", "ceo", "founder", "business", "profit", "revenue"]):
        return "business"
    
    return "general"


def _is_title_relevant(claim: str, title: str) -> bool:
    title_lower = title.lower()
    claim_lower = claim.lower()
    similarity = compute_similarity(claim, title)
    if similarity >= 0.4:
        return True

    # fallback heuristic: require substantial token overlap for titles
    tokens = [token for token in re.findall(r"[A-Za-z0-9]+", claim_lower) if len(token) >= 4]
    if not tokens:
        return claim_lower in title_lower
    matches = sum(1 for token in set(tokens) if token in title_lower)
    return matches >= max(1, len(tokens) // 2)


def classify_source(url: str, claim_type: str = "general") -> Tuple[str, int]:
    """Classify source with stricter authority for sensitive claim types."""
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    
    # Government/official sources get highest authority
    if domain.endswith(".gov") or "pib.gov.in" in domain or "eci.gov.in" in domain:
        return "Government Record", 95

    # Verified social media (Twitter, Instagram, Facebook) get high authority when they appear as official accounts
    if any(x in domain for x in ["x.com", "twitter.com", "instagram.com", "facebook.com"]):
        if claim_type == "celebrity":
            return "Verified Celebrity Account", 93
        elif claim_type == "political":
            return "Official Verified Account", 92
        return "Verified Social", 88

    # Major established news outlets including news channel websites
    if any(x in domain for x in MAJOR_NEWS_SOURCES):
        if claim_type in ["celebrity", "business"]:
            return "Established News Agency", 92
        return "Established News Agency", 90
    
    # Press releases and official websites
    if "press" in url or domain.endswith(".org"):
        return "Press Release", 85
    
    # Entertainment/blog sources - LOW authority for major claims
    if any(x in domain for x in ["vikatan.com", "maalai", "dinathanthi", "youtube.com", "reddit.com", "quora.com"]):
        # These sources are unreliable for major claims like marriages/resignations
        if claim_type in ["celebrity", "political"]:
            return "Entertainment Blog (Unreliable)", 20  # Very low for sensitive claims
        return "Entertainment Blog", 45
    
    # Generic blog/article
    if any(x in url for x in ["blog", "article"]):
        if claim_type in ["celebrity", "political"]:
            return "Casual Source (Unreliable)", 25
        return "Blog Article", 50
    
    return "Website", 60


def _normalize_domain(domain: str) -> str:
    return domain.lower().strip().replace("www.", "")


def _is_trusted_domain(domain: str) -> bool:
    normalized = _normalize_domain(domain)
    return any(normalized == trusted or normalized.endswith("." + trusted) for trusted in TRUSTED_NEWS_DOMAINS | TRUSTED_SOCIAL_DOMAINS | MAJOR_NEWS_SOURCES)


def _dedupe_results(results: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
    seen: Set[str] = set()
    unique: List[Tuple[str, str]] = []
    for url, title in results:
        if url not in seen:
            seen.add(url)
            unique.append((url, title))
    return unique


def search_trusted_news(query: str, limit: int = 6) -> List[Tuple[str, str]]:
    trusted_sites = [
        "reuters.com", "apnews.com", "bbc.com", "cnn.com", "aljazeera.com", "ndtv.com",
        "news18.com", "thehindu.com", "indianexpress.com", "hindustantimes.com", "timesofindia.com"
    ]
    site_query = " ".join(f"site:{site}" for site in trusted_sites)
    return search_bing(f"{query} {site_query}", limit)


def search_social_sites(query: str, limit: int = 6) -> List[Tuple[str, str]]:
    social_sites = ["twitter.com", "x.com", "instagram.com", "facebook.com"]
    site_query = " ".join(f"site:{site}" for site in social_sites)
    return search_bing(f"{query} {site_query}", limit)


def discover_sources_for_query(query: str) -> List[Tuple[str, str, str, int]]:
    """Discover sources with priority on official/verified sources."""
    claim_type = detect_claim_type(query)
    results: List[Tuple[str, str]] = []

    live_results = fetch_live_news(query)
    if live_results:
        results.extend(live_results)

    if len(results) < 4:
        results.extend(search_trusted_news(query, limit=6))
    if len(results) < 6:
        results.extend(search_social_sites(query, limit=6))
    if len(results) < 6:
        results.extend(search_duckduckgo(query, limit=6))
    if len(results) < 6:
        results.extend(search_bing(query, limit=6))

    results = _dedupe_results(results)
    if DEBUG:
        print(f"[Debug] Total search results after dedupe: {len(results)}")

    sources = []
    high_authority_sources = []
    low_authority_sources = []

    for url, title in results:
        if not title:
            continue
        if not _is_title_relevant(query, title):
            continue
        kind, authority = classify_source(url, claim_type)
        source_tuple = (url, title or url, kind, authority)

        if authority >= 85 and _is_trusted_domain(urlparse(url).netloc):
            high_authority_sources.append(source_tuple)
        elif authority >= 85:
            # keep high authority but lower priority if domain is not in the trusted list
            low_authority_sources.append(source_tuple)
        else:
            low_authority_sources.append(source_tuple)

    if claim_type in ["celebrity", "political"]:
        if high_authority_sources:
            sources = high_authority_sources + low_authority_sources[:2]
        else:
            sources = low_authority_sources
    else:
        sources = high_authority_sources + low_authority_sources

    return sources[:6]


def _decode_duckduckgo_redirect(href: str) -> str:
    if href.startswith("/l/?") or href.startswith("https://duckduckgo.com/l/?") or href.startswith("//duckduckgo.com/l/?"):
        parts = parse_qs(urlparse(href).query)
        uddg = parts.get("uddg")
        if uddg:
            return unquote(uddg[0])
    return href


def _extract_links(soup: BeautifulSoup, limit: int) -> List[Tuple[str, str]]:
    links: List[Tuple[str, str]] = []
    for selector in ["a.result__a", "a[data-testid='result-title-a']", "a"]:
        for anchor in soup.select(selector):
            href = anchor.get("href")
            title = anchor.get_text(strip=True)
            if not href:
                continue
            href = _decode_duckduckgo_redirect(href)
            # normalize protocol-relative URLs
            if href.startswith("//"):
                href = "https:" + href
            # skip internal duckduckgo paths
            if href.startswith("/") and not href.startswith("/l/?"):
                continue
            # derive a title when anchor text is empty
            if not title:
                try:
                    parsed = urlparse(href)
                    title = parsed.netloc or href
                except Exception:
                    title = href
            if href.startswith("http") and len(links) < limit:
                links.append((href, title))
        if links:
            break
    return links[:limit]


def search_duckduckgo(query: str, limit: int = 6) -> List[Tuple[str, str]]:
    endpoint_user_agents = [
        (
            "https://html.duckduckgo.com/html/",
            ["Mozilla/5.0 (Windows NT 10.0; Win64; x64)"]
        ),
        (
            "https://lite.duckduckgo.com/lite/",
            ["Mozilla/5.0"]
        ),
    ]
    if DEBUG:
        print(f"[Debug] DuckDuckGo search query: {query}")
    # Use a Session and prefetch the main DuckDuckGo page to establish any
    # cookies/flow that the HTML endpoints expect. Try endpoint-specific
    # user-agents until links are returned.
    session = requests.Session()
    for url, user_agents in endpoint_user_agents:
        for ua in user_agents:
            try:
                if DEBUG:
                    print(f"[Debug] Prefetching DuckDuckGo home with UA: {ua}")
                # lightweight prefetch to warm cookies and headers
                session.get("https://duckduckgo.com/", headers={"User-Agent": ua}, timeout=5)
            except Exception:
                # ignore prefetch failures
                pass
            try:
                if DEBUG:
                    print(f"[Debug] Fetching DuckDuckGo URL: {url} with User-Agent: {ua}")
                response = session.get(
                    url,
                    params={"q": query},
                    headers={"User-Agent": ua, "Referer": "https://duckduckgo.com/"},
                    timeout=10,
                )
                # allow HTML endpoints to return 202 with usable content
                try:
                    response.raise_for_status()
                except Exception:
                    if DEBUG:
                        print(f"[Debug] DuckDuckGo endpoint returned status {response.status_code}")
                soup = BeautifulSoup(response.text, "html.parser")
                links = _extract_links(soup, limit)
                if DEBUG:
                    print(f"[Debug] DuckDuckGo found {len(links)} links (UA={ua}, endpoint={url})")
                if links:
                    return links
            except Exception as exc:
                if DEBUG:
                    print(f"[Debug] DuckDuckGo fetch failed for {url} with UA {ua}: {exc}")
                continue
    return []


def search_bing(query: str, limit: int = 6) -> List[Tuple[str, str]]:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    }
    try:
        if DEBUG:
            print(f"[Debug] Bing search query: {query}")
        response = requests.get("https://www.bing.com/search", params={"q": query}, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        links = []
        for item in soup.select("li.b_algo h2 a"):
            href = item.get("href")
            title = item.get_text(strip=True)
            if href and href.startswith("http") and title:
                links.append((href, title))
                if len(links) >= limit:
                    break
        if DEBUG:
            print(f"[Debug] Bing found {len(links)} links")
        return links
    except Exception as exc:
        if DEBUG:
            print(f"[Debug] Bing fetch failed: {exc}")
        return []



