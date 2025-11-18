"""
홈페이지 관련 API
"""
from fastapi import APIRouter, Depends
from sqlmodel import Session
from typing import List
from app.schemas.youtube import HomeYoutuberCard, ChannelWithMetrics, SearchReq
from app.schemas.common import HealthCheck
from app.services.youtube_service import YouTubeService
from app.api.deps import get_db_session, get_youtube_service

router = APIRouter(prefix="/home", tags=["Home"])

@router.get("/health", response_model=HealthCheck)
def health_check():
    """서버 상태 확인"""
    return HealthCheck(status="ok", message="Home API is healthy")

@router.get("/youtubers", response_model=List[HomeYoutuberCard])
def get_home_youtubers(
    limit: int = 50,
    session: Session = Depends(get_db_session),
    youtube_service: YouTubeService = Depends(get_youtube_service)
):
    """홈 화면 유튜버 카드 리스트"""
    return youtube_service.get_home_youtubers(session, limit)

@router.post("/search", response_model=List[ChannelWithMetrics])
def search_youtubers(
    req: SearchReq,
    youtube_service: YouTubeService = Depends(get_youtube_service)
):
    """키워드로 유튜버 검색"""
    return youtube_service.search_channels(req.keyword, req.top_n)

@router.get("/popular", response_model=List[ChannelWithMetrics])
def get_popular_youtubers(
    top_n: int = 50,
    session: Session = Depends(get_db_session),
    youtube_service: YouTubeService = Depends(get_youtube_service)
):
    """인기 유튜버 조회 (DB 기반)"""
    return youtube_service.get_popular_channels_from_db(session, top_n)

@router.get("/youtubers/sorted", response_model=List[HomeYoutuberCard])
def get_sorted_youtubers(
    sort_by: str = "followers",  # followers, engagement, price
    limit: int = 50,
    session: Session = Depends(get_db_session),
    youtube_service: YouTubeService = Depends(get_youtube_service)
):
    """유튜버 정렬 조회 API
    
    Args:
        sort_by: 정렬 기준 (followers=팔로워많은순, engagement=참여율높은순, price=가격낮은순)
        limit: 조회 개수
    """
    return youtube_service.get_sorted_youtubers(session, sort_by, limit)
