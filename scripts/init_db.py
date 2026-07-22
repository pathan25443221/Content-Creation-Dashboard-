import os
from sqlmodel import SQLModel, create_engine
from config import settings

# Import models so SQLModel metadata registers them
from analytics.db.models import Video, Clip, Post, Metric

DATABASE_URL = settings.DATABASE_URL

engine = create_engine(DATABASE_URL, echo=True)

def init_db():
    print(f"Initializing database at: {DATABASE_URL}")
    SQLModel.metadata.create_all(engine)
    print("Database tables created successfully!")

if __name__ == "__main__":
    init_db()
