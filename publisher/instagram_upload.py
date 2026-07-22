import os
import sys
import uuid
import requests
from config import settings

INSTAGRAM_ACCESS_TOKEN = settings.INSTAGRAM_ACCESS_TOKEN
INSTAGRAM_BUSINESS_ACCOUNT_ID = settings.INSTAGRAM_BUSINESS_ACCOUNT_ID

def publish_to_instagram(clip_data) -> dict:
    """
    Publishes a Reel to Instagram Graph API using the 2-step media container flow.
    If Instagram credentials are missing, operates in graceful Stub mode.
    """
    title = clip_data.title if hasattr(clip_data, "title") else clip_data.get("title", "Instagram Reel")

    if not INSTAGRAM_ACCESS_TOKEN or not INSTAGRAM_BUSINESS_ACCOUNT_ID:
        print("[Instagram] Credentials (INSTAGRAM_ACCESS_TOKEN / BUSINESS_ACCOUNT_ID) not configured.")
        print("[Instagram] STUB MODE: Simulating Reel publication...")
        mock_post_id = f"ig_reel_{uuid.uuid4().hex[:8]}"
        return {"status": "success", "post_id": mock_post_id, "mode": "stub"}

    try:
        # Step 1: Create Reel container
        container_url = f"https://graph.facebook.com/v19.0/{INSTAGRAM_BUSINESS_ACCOUNT_ID}/media"
        # Note: video_url must be publicly accessible URL in production
        payload = {
            "media_type": "REELS",
            "caption": title,
            "access_token": INSTAGRAM_ACCESS_TOKEN
        }
        res = requests.post(container_url, data=payload, timeout=10)
        res_data = res.json()

        if "id" not in res_data:
            raise RuntimeError(f"Failed to create Instagram container: {res_data}")

        creation_id = res_data["id"]

        # Step 2: Publish container
        publish_url = f"https://graph.facebook.com/v19.0/{INSTAGRAM_BUSINESS_ACCOUNT_ID}/media_publish"
        pub_res = requests.post(publish_url, data={"creation_id": creation_id, "access_token": INSTAGRAM_ACCESS_TOKEN}, timeout=10)
        pub_data = pub_res.json()

        if "id" not in pub_data:
            raise RuntimeError(f"Failed to publish Instagram container: {pub_data}")

        post_id = pub_data["id"]
        print(f"[Instagram] Successfully published Reel ID: {post_id}")
        return {"status": "success", "post_id": post_id, "mode": "live"}
    except Exception as e:
        print(f"[Instagram Upload Error]: {e}", file=sys.stderr)
        raise e
