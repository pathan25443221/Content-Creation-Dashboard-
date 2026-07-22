import os
import sys
import uuid
from config import settings

CLIENT_SECRETS_FILE = settings.YOUTUBE_CLIENT_SECRETS_FILE

def publish_to_youtube(clip_data) -> dict:
    """
    Publishes a short video clip to YouTube Shorts using YouTube Data API v3.
    If OAuth client secret file is missing, operates in graceful Stub mode for local testing.
    """
    file_path = clip_data.file_path if hasattr(clip_data, "file_path") else clip_data.get("file_path")
    title = clip_data.title if hasattr(clip_data, "title") else clip_data.get("title", "Short Clip")

    if not os.path.exists(CLIENT_SECRETS_FILE):
        print(f"[YouTube] Client secrets file '{CLIENT_SECRETS_FILE}' not found.")
        print("[YouTube] STUB MODE: Simulating upload to YouTube Shorts...")
        mock_post_id = f"yt_short_{uuid.uuid4().hex[:8]}"
        return {"status": "success", "post_id": mock_post_id, "mode": "stub"}

    try:
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
        from google_auth_oauthlib.flow import InstalledAppFlow
        
        scopes = ["https://www.googleapis.com/auth/youtube.upload"]
        flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, scopes)
        creds = flow.run_local_server(port=0)

        youtube = build("youtube", "v3", credentials=creds)

        body = {
            "snippet": {
                "title": title[:100],
                "description": f"{title}\n\n#Shorts #Repurposed",
                "tags": ["Shorts", "Reels", "Content"],
                "categoryId": "22"
            },
            "status": {
                "privacyStatus": "public",
                "selfDeclaredMadeForKids": False
            }
        }

        media = MediaFileUpload(file_path, chunksize=-1, resumable=True)
        request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

        response = request.execute()
        post_id = response.get("id")
        print(f"[YouTube] Successfully uploaded video ID: {post_id}")
        return {"status": "success", "post_id": post_id, "mode": "live"}
    except Exception as e:
        print(f"[YouTube Upload Error]: {e}", file=sys.stderr)
        raise e
