"""
유튜버 상세 페이지 관련 API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from typing import List, Optional
from app.schemas.youtube import ChannelDetails, VideoStatsOut, CommentsSummaryOut
from app.core import Influencer
from app.api.deps import get_db_session

router = APIRouter(prefix="/youtuber", tags=["Youtuber Detail"])

@router.get("/{channel_id}/profile")
def get_youtuber_profile(
    channel_id: str,
    session: Session = Depends(get_db_session)
):
    """유튜버 프로필 정보"""
    influencer = session.get(Influencer, channel_id)
    if not influencer:
        raise HTTPException(status_code=404, detail="채널을 찾을 수 없습니다")
    
    return {
        "channel_id": influencer.channel_id,
        "title": influencer.title,
        "description": influencer.description,
        "subscriber_count": influencer.subscriber_count,
        "view_count": influencer.view_count,
        "video_count": influencer.video_count,
        "thumbnail_url": influencer.thumbnail_url,
        "category": influencer.category,
        "engagement_rate": influencer.engagement_rate,
        "estimated_price": influencer.estimated_price,
        "published_at": influencer.published_at
    }

@router.get("/{channel_id}/videos", response_model=List[VideoStatsOut])
def get_youtuber_videos(
    channel_id: str,
    limit: int = 10,
    session: Session = Depends(get_db_session)
):
    """유튜버 최근 영상 목록"""
    from app.core.models import Video
    from sqlmodel import select
    
    influencer = session.get(Influencer, channel_id)
    if not influencer:
        raise HTTPException(status_code=404, detail="채널을 찾을 수 없습니다")
    
    # DB에서 해당 채널의 비디오 조회
    videos = session.exec(
        select(Video).where(Video.channel_id == channel_id).limit(limit)
    ).all()
    
    return [
        VideoStatsOut(
            channel_id=video.channel_id,
            title=influencer.title,
            video_id=video.video_id,
            video_title=video.video_title,
            video_published_at=video.video_published_at.isoformat() if video.video_published_at else None,
            view_count=video.view_count,
            like_count=video.like_count,
            comment_count=video.comment_count
        )
        for video in videos
    ]

@router.get("/{channel_id}/stats")
def get_youtuber_stats(
    channel_id: str,
    session: Session = Depends(get_db_session)
):
    """유튜버 통계 정보"""
    influencer = session.get(Influencer, channel_id)
    if not influencer:
        raise HTTPException(status_code=404, detail="채널을 찾을 수 없습니다")
    
    # 기본 통계 + 계산된 ROI 지표
    avg_views = (influencer.view_count // influencer.video_count) if influencer.video_count else 0
    
    return {
        "basic_stats": {
            "subscriber_count": influencer.subscriber_count,
            "view_count": influencer.view_count,
            "video_count": influencer.video_count,
            "engagement_rate": influencer.engagement_rate
        },
        "roi_metrics": {
            "viral_score": round((influencer.engagement_rate or 0) * 10, 1),
            "avg_views": avg_views,
            "estimated_cpm": 1500,  # 기본값
            "brand_safety_score": 85,  # 기본값
            "collab_history": 0  # 기본값
        },
        "estimated_price": influencer.estimated_price,
        "category": influencer.category
    }
