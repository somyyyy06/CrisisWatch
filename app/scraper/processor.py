# backend/scraper/processor.py
import requests
from bs4 import BeautifulSoup
from transformers import pipeline
import spacy
from geopy.geocoders import Nominatim
from backend.database import SessionLocal
from backend import models
from datetime import datetime
from sqlalchemy import func

# --------------------------
# Helper: Fetch Article
# --------------------------
def fetch_url(url):
    """Fetch HTML content from a URL and extract readable text."""
    try:
        response = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # Remove scripts and styles
        for s in soup(["script", "style", "noscript"]):
            s.extract()

        # Try to extract article text
        paragraphs = soup.find_all("p")
        text = " ".join(p.get_text() for p in paragraphs)

        return text.strip() if text else response.text
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

# --------------------------
# Load Models (once per process)
# --------------------------
nlp_spacy = spacy.load("en_core_web_sm")
geolocator = Nominatim(user_agent="crisis_watch_app", timeout=10)

# Choose smaller models for local dev
classifier = pipeline("zero-shot-classification", model="typeform/distilbert-base-uncased-mnli")
summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")

CANDIDATE_LABELS = ["flood", "earthquake", "fire", "crime", "traffic", "wildfire", "protest", "other"]

# --------------------------
# Classification
# --------------------------
def classify_text(text):
    try:
        res = classifier(text[:512], candidate_labels=CANDIDATE_LABELS)
        return res["labels"][0], float(res["scores"][0])
    except Exception as e:
        print("Classification error", e)
        return "other", 0.5

# --------------------------
# Location Extraction
# --------------------------
def extract_location(text):
    doc = nlp_spacy(text[:5000])
    places = [ent.text for ent in doc.ents if ent.label_ in ("GPE", "LOC", "FAC")]
    if not places:
        return None, (None, None)
    loc_text = places[0]
    try:
        geo = geolocator.geocode(loc_text + ", India")
        if geo:
            return loc_text, (geo.longitude, geo.latitude)  # lon, lat
    except Exception as e:
        print("geocode error", e)
    return loc_text, (None, None)

# --------------------------
# Summarization
# --------------------------
def summarize_text(text):
    try:
        out = summarizer(text, max_length=80, min_length=20, do_sample=False)
        return out[0]["summary_text"]
    except Exception:
        return (text or "")[:300]

# --------------------------
# Duplicate Detection
# --------------------------
def _normalize_title(title):
    if not title:
        return ""
    return " ".join(title.lower().strip().split())

def is_duplicate(db, title, url, threshold=0.8):
    norm = _normalize_title(title)
    existing = db.query(models.ScrapedIncident).filter(
        func.lower(models.ScrapedIncident.title) == norm
    ).first()
    if existing:
        return True
    existing_url = db.query(models.ScrapedIncident).filter(
        models.ScrapedIncident.source_url == url
    ).first()
    if existing_url:
        return True
    return False

# --------------------------
# Credibility Scoring
# --------------------------
def domain_trust_score(source_url):
    if not source_url:
        return 0.8
    d = source_url.replace("www.", "")
    trusted = [
        "timesofindia.indiatimes.com",
        "ndtv.com",
        "thehindu.com",
        "hindustantimes.com",
        "reuters.com",
        "bbc.com",
    ]
    return 1.0 if any(t in d for t in trusted) else 0.8

def compute_credibility(label_score, source_url, corroboration_count=1):
    s_score = domain_trust_score(source_url)
    score = label_score * 0.7 + s_score * 0.2 + min(corroboration_count, 5) * 0.02
    return max(0.0, min(score, 1.0))

# --------------------------
# Main Processor
# --------------------------
def process_and_store(article_title, article_text, url):
    db = SessionLocal()
    try:
        if is_duplicate(db, article_title or "", url):
            return None

        label, label_score = classify_text(article_text)
        loc_text, (lon, lat) = extract_location(article_text)
        summary = summarize_text(article_text)

        credibility = compute_credibility(label_score, url, corroboration_count=1)

        row = models.ScrapedIncident(
            title=article_title or (url[-80:]),
            description=(article_text or "")[:4000],
            incident_type=label,
            source_url=url,
            location_text=loc_text,
            lon=lon,
            lat=lat,
            credibility_score=credibility,
            summary=summary
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return row
    finally:
        db.close()
