import os
from sqlmodel import SQLModel, create_engine
from config import settings

# Import models so SQLModel metadata registers them
from analytics.db.models import Video, Clip, Post, Metric

DATABASE_URL = settings.DATABASE_URL

engine = create_engine(DATABASE_URL, echo=False)

from sqlalchemy import text

def init_db():
    print(f"Initializing database at: {DATABASE_URL}")
    SQLModel.metadata.create_all(engine)
    
    # Auto-migrate SQLite schema if new column is missing on existing tables
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE clip ADD COLUMN virality_score REAL DEFAULT 8.5;"))
            conn.commit()
            print("Successfully added missing 'virality_score' column to 'clip' table.")
        except Exception:
            # Column already exists
            pass
            
    print("Database tables created & migrated successfully!")

if __name__ == "__main__":
    init_db()
