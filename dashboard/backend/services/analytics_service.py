from datetime import datetime, timedelta
from sqlmodel import Session, select, func
from analytics.db.models import Clip, Post, Metric

def get_overview_stats(session: Session) -> dict:
    total_clips = session.exec(select(func.count(Clip.id))).one()
    pending_review_count = session.exec(
        select(func.count(Clip.id)).where(Clip.status == "pending")
    ).one()

    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    recent_posts_count = session.exec(
        select(func.count(Post.id)).where(Post.posted_at >= seven_days_ago)
    ).one()

    metrics_sum = session.exec(
        select(func.sum(Metric.views), func.sum(Metric.likes))
    ).one()

    total_views = metrics_sum[0] or 0
    total_likes = metrics_sum[1] or 0

    recent_clips = session.exec(
        select(Clip).order_by(Clip.created_at.desc()).limit(5)
    ).all()

    return {
        "total_clips": total_clips,
        "pending_review_count": pending_review_count,
        "recent_posts_count": recent_posts_count,
        "total_views": total_views,
        "total_likes": total_likes,
        "recent_activity": [
            {
                "id": c.id,
                "title": c.title or f"Clip #{c.id}",
                "status": c.status,
                "created_at": c.created_at.isoformat()
            }
            for c in recent_clips
        ]
    }

def list_posts_with_metrics(session: Session) -> list:
    posts = session.exec(select(Post).order_by(Post.id.desc())).all()
    result = []
    for p in posts:
        clip = session.get(Clip, p.clip_id)
        metrics = session.exec(
            select(Metric).where(Metric.post_id == p.id).order_by(Metric.fetched_at.desc())
        ).first()

        result.append({
            "id": p.id,
            "clip_id": p.clip_id,
            "clip_title": clip.title if clip else "Clip",
            "platform": p.platform,
            "platform_post_id": p.platform_post_id,
            "posted_at": p.posted_at.isoformat() if p.posted_at else None,
            "status": p.status,
            "error_message": p.error_message,
            "latest_metrics": {
                "views": metrics.views if metrics else 0,
                "likes": metrics.likes if metrics else 0,
                "comments": metrics.comments if metrics else 0,
                "reach": metrics.reach if metrics else None
            } if metrics else None
        })
    return result
