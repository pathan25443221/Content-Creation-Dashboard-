from fastapi import APIRouter
from sqlmodel import Session, create_engine
from config import settings

from dashboard.backend.services.analytics_service import get_overview_stats, list_posts_with_metrics
from analytics.scheduler import poll_all_post_metrics

engine = create_engine(settings.DATABASE_URL, echo=False)
router = APIRouter()

@router.get("/overview")
def get_overview():
    """Summary metrics for the Home/Overview screen."""
    with Session(engine) as session:
        return get_overview_stats(session)

@router.get("/posts")
def list_posts():
    """Returns library of all published and queued posts."""
    with Session(engine) as session:
        return list_posts_with_metrics(session)

@router.post("/poll")
def trigger_metrics_poll():
    """Polls latest analytics from connected social platforms."""
    poll_all_post_metrics()
    return {"message": "Metrics poll triggered successfully."}
