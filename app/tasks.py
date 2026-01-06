from .celery_app import celery
from .database import SessionLocal
from . import crud, models
from .ml.inference import get_credibility_score
import os

@celery.task
def process_raw_post(text, source=None):
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
