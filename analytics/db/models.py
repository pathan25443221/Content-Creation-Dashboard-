from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship

class Video(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    source_url: str
    downloaded_at: datetime = Field(default_factory=datetime.utcnow)
    video_type: str  # "speech" or "visual"
    local_path: Optional[str] = None
    title: Optional[str] = None

    clips: List["Clip"] = Relationship(back_populates="video")

class Clip(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    video_id: int = Field(foreign_key="video.id")
    start_time: float
    end_time: float
    reason: str
    file_path: str
    title: Optional[str] = None
    description: Optional[str] = None
    hashtags: Optional[str] = None
    virality_score: Optional[float] = Field(default=8.5)
    status: str = Field(default="pending")  # "pending", "approved", "rejected"
    created_at: datetime = Field(default_factory=datetime.utcnow)

    video: Optional[Video] = Relationship(back_populates="clips")
    posts: List["Post"] = Relationship(back_populates="clip")

class Post(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    clip_id: int = Field(foreign_key="clip.id")
    platform: str  # "youtube" or "instagram"
    platform_post_id: Optional[str] = None
    posted_at: Optional[datetime] = None
    status: str = Field(default="queued")  # "queued", "posted", "failed"
    error_message: Optional[str] = None

    clip: Optional[Clip] = Relationship(back_populates="posts")
    metrics: List["Metric"] = Relationship(back_populates="post")

class Metric(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    post_id: int = Field(foreign_key="post.id")
    fetched_at: datetime = Field(default_factory=datetime.utcnow)
    views: int = Field(default=0)
    likes: int = Field(default=0)
    comments: int = Field(default=0)
    reach: Optional[int] = Field(default=None)

    post: Optional[Post] = Relationship(back_populates="metrics")
