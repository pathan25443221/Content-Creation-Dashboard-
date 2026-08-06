import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlmodel import Session, select, create_engine
from analytics.db.models import Clip, Post
from config import settings

engine = create_engine(settings.DATABASE_URL, echo=False)

def rollback_failed_clips():
    with Session(engine) as session:
        failed_posts = session.exec(select(Post).where(Post.status == "failed")).all()
        
        clips_restored = 0
        for post in failed_posts:
            clip = session.get(Clip, post.clip_id)
            if clip and clip.status == "approved":
                clip.status = "pending"
                session.add(clip)
                clips_restored += 1
            session.delete(post)
            
        session.commit()
        print(f"Successfully restored {clips_restored} clips back to the Review Queue!")

if __name__ == "__main__":
    rollback_failed_clips()
