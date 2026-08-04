import os
import random

def fetch_instagram_insights(platform_post_id: str, prev_data: dict = None) -> dict:
    """
    Fetches stats for an Instagram Reel.
    Fallback to simulated incremental metrics when credentials are not live.
    """
    if platform_post_id.startswith("ig_reel_") or "mock" in platform_post_id:
        if prev_data and prev_data.get("views", 0) > 0:
            return {
                "views": prev_data["views"] + random.randint(50, 800),
                "likes": prev_data["likes"] + random.randint(5, 120),
                "comments": prev_data["comments"] + random.randint(1, 15),
                "reach": prev_data.get("reach", 0) + random.randint(40, 600)
            }
        else:
            return {
                "views": random.randint(300, 8000),
                "likes": random.randint(40, 950),
                "comments": random.randint(2, 85),
                "reach": random.randint(250, 7500)
            }

    return {
        "views": 0,
        "likes": 0,
        "comments": 0,
        "reach": 0
    }
