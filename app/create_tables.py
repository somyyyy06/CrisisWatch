# create_tables.py
from app.models import Base
from app.database import engine

# This will create all tables defined in your models (users, etc.)
Base.metadata.create_all(bind=engine)
print("✅ Tables created successfully!")
