from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class ProjectCreateReq(BaseModel):
    company_name: str
    brand_categories: str  # 단순 문자열
    brand_tone: str
    campaign_goal: str

class ProjectInfo(BaseModel):
    project_id: str
    company_name: str
    brand_categories: str
    brand_tone: str
    campaign_goal: str
    created_at: datetime
    total_youtubers: int  # 분석된 유튜버 수

class YoutuberWithROI(BaseModel):
    channel_id: str
    title: str
    subscriber_count: Optional[int] = None
    thumbnail_url: Optional[str] = None
    category: str = "미분류"
    engagement_rate: Optional[float] = None
    estimated_price: str = "가격 문의"
    total_score: float  # roi_score -> total_score로 변경
    grade: str   # roi_grade -> grade로 변경 (더 간결)
