# backend/scraper/rss_scraper.py
import feedparser
from urllib.parse import urlparse, urlunparse
import re
import time

from .processor import fetch_url

try:
    from newspaper import Article
    HAVE_NEWSPAPER = True
except Exception:
    HAVE_NEWSPAPER = False

from bs4 import BeautifulSoup


RSS_SOURCES = [
    "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
    "https://www.ndtv.com/rss",
]


def fetch_items(max_items: int = 200):
    items = []
    for url in RSS_SOURCES:
        d = feedparser.parse(url)
        for e in d.entries:
            items.append(
                {
                    "title": e.get("title"),
                    "link": e.get("link"),
                    "published": e.get("published", None),
                    "source": urlparse(e.get("link") or "").netloc,
                }
            )
    return items[:max_items]


def _clean_text(text: str) -> str:
    if not text:
        return text

    text = re.sub(r"\s+", " ", text).strip()
    boilerplate = [
        "Follow the TOI News Desk",
        "Subscribe to our newsletter",
        "Read more on",
        "Follow us on",
        "Download The Times of India News App",
        "Copyright ©",
        "All Rights Reserved",
        "For more details, visit",
    ]
    for p in boilerplate:
        text = text.replace(p, "")
    return text.strip()


def _extract_from_soup(html: str, min_paragraph_len: int = 30) -> str:
    try:
        soup = BeautifulSoup(html, "html.parser")
        for s in soup(["script", "style", "noscript"]):
            s.extract()

        paragraphs = soup.find_all("p")
        meaningful = [
            p.get_text().strip()
            for p in paragraphs
            if len(p.get_text().strip()) >= min_paragraph_len
        ]
        if meaningful:
            return _clean_text(" ".join(meaningful))
    except Exception:
        pass
    return ""


def _try_newspaper(url: str):
    if not HAVE_NEWSPAPER:
        return None, None
    try:
        art = Article(url, language="en")
        art.download()
        art.parse()
        text = _clean_text(art.text or "")
        if text and len(text) > 40:
            return art.title or None, text
    except Exception as e:
        print("newspaper3k error:", e)
    return None, None


def _try_mobile_timesofindia(parsed_url):
    try:
        mobile_netloc = "m.timesofindia.com"
        mobile_url = urlunparse(parsed_url._replace(netloc=mobile_netloc))
        html = fetch_url(mobile_url)
        if html:
            text = _extract_from_soup(html, min_paragraph_len=20)
            if text and len(text) > 50:
                return mobile_url, text
    except Exception as e:
        print("mobile TOI error:", e)
    return None, ""


def fetch_article_text(url: str, rss_title: str = None):
    title = rss_title
    parsed = urlparse(url)

    n_title, n_text = _try_newspaper(url)
    if n_text:
        return title or n_title, n_text, url

    if "timesofindia.indiatimes.com" in parsed.netloc.lower():
        m_url, m_text = _try_mobile_timesofindia(parsed)
        if m_text:
            return title, m_text, m_url or url

    html = fetch_url(url)
    if html:
        text = _extract_from_soup(html, min_paragraph_len=30)
        if text and len(text) > 60:
            return title, text, url

    html = fetch_url(url)
    if html:
        text = _extract_from_soup(html, min_paragraph_len=10)
        if text and len(text) > 40:
            return title, text, url

    return None, None, url


if __name__ == "__main__":
    items = fetch_items(50)
    print(f"Found {len(items)} RSS items")
    for i, it in enumerate(items[:8], 1):
        print(f"\n[{i}] {it['link']}")
        t, text, out_url = fetch_article_text(it["link"], it["title"])
        print("Title:", t)
        print("Text length:", len(text) if text else 0)
        time.sleep(0.8)
