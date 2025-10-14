# backend/scraper/rss_scraper.py
import feedparser
from urllib.parse import urlparse, urlunparse
import re
import time

# We call fetch_url from processor which has a robust requests-based fetcher
from backend.scraper.processor import fetch_url

# Optional: newspaper extraction (best effort)
try:
    from newspaper import Article
    HAVE_NEWSPAPER = True
except Exception:
    HAVE_NEWSPAPER = False

# BeautifulSoup fallback
from bs4 import BeautifulSoup

# RSS sources — add/remove as needed
RSS_SOURCES = [
    "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
    "https://www.ndtv.com/rss",
]


def fetch_items(max_items: int = 200):
    """
    Fetch RSS entries from RSS_SOURCES and return list of dicts:
    { "title", "link", "published", "source" }
    """
    items = []
    for url in RSS_SOURCES:
        d = feedparser.parse(url)
        for e in d.entries:
            items.append({
                "title": e.get("title"),
                "link": e.get("link"),
                "published": e.get("published", None),
                "source": urlparse(e.get("link") or "").netloc
            })
    return items[:max_items]


def _clean_text(text: str) -> str:
    """Normalize whitespace and remove obvious boilerplate phrases."""
    if not text:
        return text
    text = re.sub(r'\s+', ' ', text).strip()

    boilerplate_phrases = [
        "Follow the TOI News Desk",
        "Subscribe to our newsletter",
        "Read more on",
        "Follow us on",
        "Download The Times of India News App",
        "Copyright ©",
        "All Rights Reserved",
        "For more details, visit",
    ]
    for p in boilerplate_phrases:
        text = text.replace(p, "")
    text = text.strip()
    return text


def _extract_from_soup(html: str, min_paragraph_len: int = 30) -> str:
    """Generic paragraph-based extraction using BeautifulSoup"""
    try:
        soup = BeautifulSoup(html, "html.parser")
        # remove scripts/styles
        for s in soup(["script", "style", "noscript"]):
            s.extract()
        paragraphs = soup.find_all("p")
        meaningful = [p.get_text().strip() for p in paragraphs if len(p.get_text().strip()) >= min_paragraph_len]
        if meaningful:
            text = " ".join(meaningful)
            return _clean_text(text)
    except Exception:
        pass
    return ""


def _try_newspaper(url: str):
    """Try extraction using newspaper3k (if installed). Returns (title, text) or (None, None)."""
    if not HAVE_NEWSPAPER:
        return None, None
    try:
        art = Article(url, language="en")
        art.download()
        art.parse()
        text = art.text or ""
        title = art.title or None
        text = _clean_text(text)
        if text and len(text) > 40:
            return title, text
    except Exception as e:
        # don't crash on newspaper failures
        print("newspaper3k extraction error:", e)
    return None, None


def _try_mobile_timesofindia(parsed_url):
    """
    Build a mobile TOI URL and try to fetch it. TOI often serves lighter HTML on mobile subdomain.
    """
    try:
        # construct mobile netloc: m.timesofindia.com
        mobile_netloc = "m.timesofindia.com"
        mobile_parsed = parsed_url._replace(netloc=mobile_netloc)
        mobile_url = urlunparse(mobile_parsed)
        html = fetch_url(mobile_url)
        if html:
            text = _extract_from_soup(html, min_paragraph_len=20)
            if text and len(text) > 50:
                return mobile_url, text
    except Exception as e:
        print("mobile TOI fallback error:", e)
    return None, ""


def fetch_article_text(url: str, rss_title: str = None):
    """
    Multi-strategy text extraction:
      1) newspaper3k (fast/good)
      2) site-specific mobile fallback for timesofindia
      3) generic fetch_url() + BeautifulSoup paragraph extraction
    Returns (title, text, url)
    """
    title = rss_title or None
    content_text = None

    parsed = urlparse(url)

    # Strategy 1: newspaper3k
    try:
        n_title, n_text = _try_newspaper(url)
        if n_text:
            title = title or n_title
            return title, n_text, url
    except Exception:
        pass

    # Strategy 2: special-case mobile TOI if the domain is timesofindia.indiatimes.com
    try:
        if "timesofindia.indiatimes.com" in parsed.netloc.lower():
            mobile_url, mobile_text = _try_mobile_timesofindia(parsed)
            if mobile_text and len(mobile_text) > 50:
                title = title or None
                return title, mobile_text, mobile_url or url
    except Exception:
        pass

    # Strategy 3: generic fetch + soup extraction
    try:
        html = fetch_url(url)
        if html:
            gs_text = _extract_from_soup(html, min_paragraph_len=30)
            if gs_text and len(gs_text) > 60:
                title = title or None
                return title, gs_text, url
    except Exception as e:
        print("generic fetch+bs4 error:", e)

    # Strategy 4: try a more permissive BS4 scrape of shorter paragraphs (last resort)
    try:
        html = fetch_url(url)
        if html:
            gs_text = _extract_from_soup(html, min_paragraph_len=10)
            if gs_text and len(gs_text) > 40:
                title = title or None
                return title, gs_text, url
    except Exception:
        pass

    # Nothing worked
    return None, None, url


if __name__ == "__main__":
    # quick local test (prints preview for first few RSS items)
    items = fetch_items(50)
    print(f"Found {len(items)} RSS items")
    for i, it in enumerate(items[:8], 1):
        print(f"\n[{i}/{min(8,len(items))}] URL: {it['link']}")
        t, text, out_url = fetch_article_text(it['link'], it['title'])
        print("Title:", t)
        print("Out URL:", out_url)
        print("Text length:", len(text) if text else 0)
        if text:
            print("Preview:", text[:300].replace("\n", " "))
        time.sleep(0.8)
