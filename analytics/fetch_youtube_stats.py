import os
import random
from datetime import datetime

def fetch_youtube_stats(platform_post_id: str, prev_data: dict = None) -> dict:
    """
    Fetches stats (views, likes, comments) for a YouTube Short.
    Fallback to simulated incremental metrics when credentials are not live or for mock IDs.
    """
    if platform_post_id.startswith("yt_short_") or "mock" in platform_post_id:
        if prev_data and prev_data.get("views", 0) > 0:
            # Simulate organic growth
            return {
                "views": prev_data["views"] + random.randint(15, 300),
                "likes": prev_data["likes"] + random.randint(2, 45),
                "comments": prev_data["comments"] + random.randint(0, 5),
                "reach": None
            }
        else:
            # Initial viral burst
            return {
                "views": random.randint(150, 4500),
                "likes": random.randint(12, 380),
                "comments": random.randint(1, 45),
                "reach": None
            }

    # Live API implementation
    try:
        from config import settings
        from googleapiclient.discovery import build
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        import sys

        CLIENT_SECRETS_FILE = settings.YOUTUBE_CLIENT_SECRETS_FILE
        TOKEN_FILE = getattr(settings, 'YOUTUBE_OAUTH_TOKEN_FILE', 'publisher/credentials/youtube_token.json')
        # Use full youtube scope so we only authenticate once for both uploading and reading stats
        scopes = ["https://www.googleapis.com/auth/youtube"]

        creds = None
        if os.path.exists(TOKEN_FILE):
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, scopes)
            
        # Check if creds are missing, invalid, or lack the required scopes
        if not creds or not creds.valid or not creds.has_scopes(scopes):
            if creds and creds.expired and creds.refresh_token and creds.has_scopes(scopes):
                creds.refresh(Request())
            else:
                if not os.path.exists(CLIENT_SECRETS_FILE):
                    print(f"[YouTube Analytics] Client secrets file missing at {CLIENT_SECRETS_FILE}. Using fallback.", file=sys.stderr)
                    return {"views": 0, "likes": 0, "comments": 0, "reach": None}
                    
                print("[YouTube Analytics] Missing or insufficient scopes. Requesting new login...", file=sys.stderr)
                flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, scopes)
                creds = flow.run_local_server(port=0)
            
            with open(TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())

        youtube = build("youtube", "v3", credentials=creds)
        
        request = youtube.videos().list(
            part="statistics",
            id=platform_post_id
        )
        response = request.execute()
        
        if "items" in response and len(response["items"]) > 0:
            stats = response["items"][0]["statistics"]
            return {
                "views": int(stats.get("viewCount", 0)),
                "likes": int(stats.get("likeCount", 0)),
                "comments": int(stats.get("commentCount", 0)),
                "reach": None
            }
        else:
            print(f"[YouTube Analytics] Video {platform_post_id} not found via API.", file=sys.stderr)
            return {"views": 0, "likes": 0, "comments": 0, "reach": None}
            
    except Exception as e:
        print(f"[YouTube Analytics Error]: {e}", file=sys.stderr)
        return {"views": 0, "likes": 0, "comments": 0, "reach": None}
