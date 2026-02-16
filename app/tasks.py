from .celery_app import celery
from .database import SessionLocal
from . import crud, models
import os

@celery.task
def process_raw_post(text, source=None):
    from .ml.inference import get_credibility_score

    db = SessionLocal()
    try:
        cred = get_credibility_score(text)
        created = crud.create_incident(
            db=db,
            title=f"Auto: {text[:20]}",
            description=text,
            disaster_type="Unknown",
            credibility_score=cred,
            lon=77.0, lat=28.0
        )
    finally:
        db.close()
    return created.id


@celery.task
def notify_user_email(user_id, incident_id):
    db = SessionLocal()
    try:
        user = db.query(models.User).get(user_id)
        incident = db.query(models.Incident).get(incident_id)
        if not user or not incident:
            return

        body = f"""
        New incident near you:
        {incident.title}
        {incident.description}
        Credibility: {incident.credibility_score}
        """

        # Dev mode: just log/print
        print(f"🔔 NOTIFY {user.email}: {body.strip()}")

        # Later: enable SMTP sending
        # smtp_host = os.getenv("SMTP_HOST", "smtp.example.com")
        # smtp_user = os.getenv("SMTP_USER")
        # smtp_pass = os.getenv("SMTP_PASS")
        # with smtplib.SMTP(smtp_host) as s:
        #     s.login(smtp_user, smtp_pass)
        #     s.sendmail("from@example.com", user.email, f"Subject: New Incident\n\n{body}")

    finally:
        db.close()


@celery.task
def scrape_and_store_news():
    """
    Celery Beat task that runs every 24 hours.
    Fetches RSS feeds and stores new incidents in the database.
    """
    from .scraper.rss_scraper import fetch_items, fetch_article_text
    from .scraper.processor import process_and_store

    print("🔄 Starting news scrape task...")
    
    try:
        # Fetch RSS items (up to 200)
        items = fetch_items(max_items=200)
        print(f"📰 Fetched {len(items)} RSS items")
        
        processed_count = 0
        skipped_count = 0
        error_count = 0
        
        for item in items:
            try:
                url = item.get("link")
                rss_title = item.get("title")
                
                if not url:
                    skipped_count += 1
                    continue
                
                # Fetch full article text
                title, text, final_url = fetch_article_text(url, rss_title)
                
                if not text or not title:
                    skipped_count += 1
                    continue
                
                # Process and store using existing processor
                result = process_and_store(title, text, final_url)
                
                if result:
                    processed_count += 1
                    print(f"✅ Stored: {title[:60]}...")
                else:
                    skipped_count += 1
                    
            except Exception as e:
                error_count += 1
                print(f"❌ Error processing item: {e}")
                continue
        
        print(f"✅ Scrape complete: {processed_count} new articles, {skipped_count} skipped, {error_count} errors")
        return {
            "processed": processed_count,
            "skipped": skipped_count,
            "errors": error_count
        }
        
    except Exception as e:
        print(f"❌ Scrape task failed: {e}")
        return {"error": str(e)}
