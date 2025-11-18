"""
API 의존성 관리
"""
from sqlmodel import Session
from app.core import get_session
from app.services import youtube_service, brand_service, roi_service

# 데이터베이스 세션 의존성
def get_db_session():
    """데이터베이스 세션 의존성"""
    yield from get_session()

# 서비스 의존성들
def get_youtube_service():
    """YouTube 서비스 의존성"""
    return youtube_service

def get_brand_service():
    """브랜드 서비스 의존성"""
    return brand_service

def get_roi_service():
    """ROI 서비스 의존성"""
    return roi_service
