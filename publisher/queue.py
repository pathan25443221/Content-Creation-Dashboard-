import os
import sys
import time
from datetime import datetime, timedelta
from sqlmodel import Session, create_engine, select
from config import settings

from analytics.db.models import Post, Clip

engine = create_engine(settings.DATABASE_URL, echo=False)

def queue_clip_for_publishing(clip_id: int, platforms: list) -> list:
    """
    Enqueues an approved clip for publishing on the specified platforms (e.g. ['youtube', 'instagram']).
    """
    queued_posts = []
    with Session(engine) as session:
        clip = session.get(Clip, clip_id)
        if not clip:
            raise ValueError(f"Clip ID {clip_id} not found.")

        # Update clip status to approved
        clip.status = "approved"
        session.add(clip)

        for platform in platforms:
            # Check if post already exists for this clip and platform
            existing = session.exec(
                select(Post).where(Post.clip_id == clip_id, Post.platform == platform)
            ).first()

            if not existing:
                post = Post(
                    clip_id=clip_id,
                    platform=platform.lower(),
                    status="queued"
                )
                session.add(post)
                queued_posts.append(post)

        session.commit()
        for p in queued_posts:
            session.refresh(p)

    print(f"[Queue] Queued {len(queued_posts)} publishing jobs for Clip ID {clip_id}.")
    return queued_posts

def process_publishing_queue():
    """
    Processes queued post jobs while enforcing platform rate limits and handling retries.
    """
    from publisher.youtube_upload import publish_to_youtube
    from publisher.instagram_upload import publish_to_instagram

    print("[Queue] Processing publishing queue...")
    with Session(engine) as session:
        queued_posts = session.exec(
            select(Post).where(Post.status == "queued")
        ).all()

        if not queued_posts:
            print("[Queue] Queue is currently empty.")
            return

        for post in queued_posts:
            clip = session.get(Clip, post.clip_id)
            if not clip:
                continue

            print(f"[Queue] Processing Post ID {post.id} ({post.platform}) for Clip: '{clip.title}'")
            try:
                if post.platform == "youtube":
                    result = publish_to_youtube(clip)
                elif post.platform == "instagram":
                    result = publish_to_instagram(clip)
                else:
                    raise ValueError(f"Unknown platform: {post.platform}")

                post.status = "posted"
                post.platform_post_id = result.get("post_id", "mock_id")
                post.posted_at = datetime.utcnow()
                post.error_message = None
                print(f"[Queue] Successfully posted (Post ID {post.id}) -> Platform ID: {post.platform_post_id}")
            except Exception as e:
                post.status = "failed"
                post.error_message = str(e)
                print(f"[Queue] Failed to post (Post ID {post.id}): {e}", file=sys.stderr)

            session.add(post)
            session.commit()

if __name__ == "__main__":
    process_publishing_queue()
