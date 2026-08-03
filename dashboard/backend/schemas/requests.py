from typing import Optional, List
from pydantic import BaseModel

class GenerateRequest(BaseModel):
    video_input: str
    video_type: str = "speech"
    burn_captions: bool = True
    quantity: int = 3
    quality: str = "high"
    caption_color: str = "white"
    caption_animation: str = "none"

class ApproveRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    hashtags: Optional[str] = None
    platforms: List[str] = ["youtube", "instagram"]
