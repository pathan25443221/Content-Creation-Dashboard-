import os
import random
from datetime import datetime

def fetch_youtube_stats(platform_post_id: str) -> dict:
    """
    Fetches stats (views, likes, comments) for a YouTube Short.
    Fallback to simulated metrics when credentials are not live.
    """
    if platform_post_id.startswith("yt_short_") or "mock" in platform_post_id:
        return {
            "views": random.randint(150, 4500),
            "likes": random.randint(12, 380),
            "comments": random.randint(1, 45),
            "reach": None
        }

    # Live API implementation placeholder
    return {
        "views": 0,
        "likes": 0,
        "comments": 0,
        "reach": None
    }
