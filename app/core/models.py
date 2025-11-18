from sqlmodel import SQLModel, Field, Relationship
from typing import List, Optional
from datetime import datetime

# Video 테이블과 Influencer 간의 관계를 위한 중간 테이블
class VideoLink(SQLModel, table=True):
    video_id: Optional[str] = Field(default=None, foreign_key="video.video_id", primary_key=True)
    influencer_id: Optional[str] = Field(default=None, foreign_key="influencer.channel_id", primary_key=True)

# Video 테이블 정의 
class Video(SQLModel, table=True):
    video_id: str = Field(primary_key=True)
    video_title: Optional[str] = None
    video_published_at: Optional[datetime] = None
    view_count: Optional[int] = None
    like_count: Optional[int] = None
    comment_count: Optional[int] = None

    # Influencer와의 관계
    channel_id: Optional[str] = Field(default=None, foreign_key="influencer.channel_id")
    channel: Optional["Influencer"] = Relationship(back_populates="videos")

# Influencer 테이블 정의
class Influencer(SQLModel, table=True):
    channel_id: str = Field(primary_key=True)
    title: Optional[str] = None
    description: Optional[str] = None 
    subscriber_count: Optional[int] = None
    view_count: Optional[int] = None
    video_count: Optional[int] = None
    thumbnail_url: Optional[str] = None
    published_at: Optional[datetime] = None
    country: Optional[str] = None

    # 추가 컬럼들
    category: Optional[str] = None
    estimated_price: Optional[str] = None
    engagement_rate: Optional[float] = None
    last_updated: Optional[datetime] = None

    # ROI 분석 컬럼들
    viral_score: Optional[float] = None
    avg_views: Optional[int] = None
    estimated_cpm: Optional[float] = None
    brand_safety_score: Optional[float] = None
    collab_history: Optional[bool] = None

    # Video와의 관계
    videos: List[Video] = Relationship(back_populates="channel")

# 프로젝트 테이블 (브랜드 정보)
class Project(SQLModel, table=True):
    project_id: str = Field(primary_key=True)
    company_name: str  # 회사명
    brand_categories: str  # JSON 문자열로 저장 ["건강/의료", "뷰티/화장품"]
    brand_tone: str  # "친화적", "프리미엄", "럭셔리"
    campaign_goal: str  # 캠페인 목표
    brand_image_path: Optional[str] = None  # 브랜드 이미지 파일 경로
    created_at: Optional[datetime] = Field(default_factory=datetime.now)

# 프로젝트별 유튜버 ROI 결과
class ProjectResult(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: str = Field(foreign_key="project.project_id")
    channel_id: str = Field(foreign_key="influencer.channel_id")
    roi_score: float  # 0-100 점수
    roi_grade: str   # S, A, B, C, D
