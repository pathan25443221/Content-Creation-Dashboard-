import os
import time
from datetime import datetime
from sqlmodel import Session, create_engine, select
from config import settings
from analytics.db.models import Post, Metric
from analytics.fetch_youtube_stats import fetch_youtube_stats
from analytics.fetch_instagram_insights import fetch_instagram_insights

engine = create_engine(settings.DATABASE_URL, echo=False)

def poll_all_post_metrics():
    """
    Polls social platform stats for all published posts and stores metrics in DB.
    """
    print(f"[Analytics] Starting scheduled metrics poll at {datetime.utcnow().isoformat()}...")
    with Session(engine) as session:
        posts = session.exec(select(Post).where(Post.status == "posted")).all()
        
        if not posts:
            print("[Analytics] No posted clips found to poll.")
            return

        metrics_added = 0
        for post in posts:
            if not post.platform_post_id:
                continue

            # Get the previous metric snapshot to simulate incremental growth in mocks
            previous = session.exec(
                select(Metric).where(Metric.post_id == post.id).order_by(Metric.fetched_at.desc())
            ).first()
            
            prev_data = {
                "views": previous.views if previous else 0,
                "likes": previous.likes if previous else 0,
                "comments": previous.comments if previous else 0
            }

            if post.platform == "youtube":
                stats = fetch_youtube_stats(post.platform_post_id, prev_data)
            elif post.platform == "instagram":
                stats = fetch_instagram_insights(post.platform_post_id, prev_data)
            else:
                continue

            metric_entry = Metric(
                post_id=post.id,
                fetched_at=datetime.utcnow(),
                views=stats.get("views", 0),
                likes=stats.get("likes", 0),
                comments=stats.get("comments", 0),
                reach=stats.get("reach")
            )
            session.add(metric_entry)
            metrics_added += 1

        session.commit()
        print(f"[Analytics] Recorded {metrics_added} new metric records.")

if __name__ == "__main__":
    poll_all_post_metrics()
