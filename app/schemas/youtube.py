from typing import List, Optional
from pydantic import BaseModel, Field

# 요청 스키마
class SearchReq(BaseModel):
    keyword: str
    top_n: int = Field(30, ge=1, le=200)
    region: str = "KR"
    lang: str = "ko"

class KRPopularReq(BaseModel):
    top_n: int = 50
    region: str = "KR"
    pages: int = 5

class VideoStatsReq(BaseModel):
    channel_ids: Optional[List[str]] = None
    video_ids: Optional[List[str]] = None
    max_videos_per_channel: int = 8

class CommentsSummaryReq(BaseModel):
    channel_id: str
    max_videos: int = Field(5, ge=1, le=20)
    max_comments_per_video: int = Field(50, ge=10, le=200)

# 응답 스키마
class ChannelDetails(BaseModel):
    channel_id: str
    title: Optional[str] = None
    description: Optional[str] = None
    custom_url: Optional[str] = None
    published_at: Optional[str] = None
    country: Optional[str] = None
    subscriber_count: Optional[int] = None
    video_count: Optional[int] = None
    view_count: Optional[int] = None
    topic_ids: Optional[List[str]] = None
    thumbnail_url: Optional[str] = None
    source: Optional[str] = None

class VideoStatsOut(BaseModel):
    channel_id: Optional[str] = None
    title: Optional[str] = None  # channel_title -> title로 통일
    video_id: str
    video_title: Optional[str] = None
    video_published_at: Optional[str] = None
    view_count: Optional[int] = None
    like_count: Optional[int] = None
    comment_count: Optional[int] = None
    duration_seconds: Optional[int] = None

class HomeYoutuberCard(BaseModel):
    channel_id: str
    title: str  # channel_title -> title로 통일
    subscriber_count: Optional[int] = None
    thumbnail_url: Optional[str] = None
    category: str = "미분류"
    engagement_rate: Optional[float] = None
    estimated_price: str = "가격 문의"

class ChannelWithMetrics(BaseModel):
    channel_id: str
    title: str
    subscriber_count: Optional[int] = None
    view_count: Optional[int] = None
    video_count: Optional[int] = None
    thumbnail_url: Optional[str] = None
    engagement_rate: Optional[float] = None
    estimated_price: Optional[str] = None
    category: Optional[str] = None

class CommentsSummaryOut(BaseModel):
    channel_id: str
    total_comments: int
    avg_sentiment_score: float
    sentiment_distribution: dict
    top_keywords: List[str]
    sample_comments: List[str]
