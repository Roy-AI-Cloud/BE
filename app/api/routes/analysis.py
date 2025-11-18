"""
분석 페이지 관련 API (프로젝트 기반)
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.schemas.roi import BrandImageScore, SentimentScore, ROIEstimate, TotalScore
from app.core.models import Influencer, Project, ProjectResult
from app.api.deps import get_db_session
import json

router = APIRouter(prefix="/analysis", tags=["Analysis"])

@router.get("/brand-match/{project_id}/{channel_id}", response_model=BrandImageScore)
def analyze_brand_compatibility(
    project_id: str,
    channel_id: str,
    session: Session = Depends(get_db_session)
):
    """브랜드 적합도 분석 (실제 CLIP + 텍스트 분석)"""
    
    from app.core.models import Video
    from app.services.brand_service import brand_service
    
    # 프로젝트 정보 조회
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다")
    
    # 채널 정보 조회
    influencer = session.get(Influencer, channel_id)
    if not influencer:
        raise HTTPException(status_code=404, detail="채널을 찾을 수 없습니다")
    
    # 비디오 데이터 조회
    videos = session.exec(
        select(Video).where(Video.channel_id == channel_id)
    ).all()
    
    # 비디오 제목들 수집
    video_titles = [video.video_title for video in videos if video.video_title]
    
    # 썸네일 이미지 로드 (유튜버 프로필 썸네일 사용)
    channel_thumbnails = []
    if influencer.thumbnail_url:
        try:
            from app.ml import load_image_from_url
            thumbnail_image = load_image_from_url(influencer.thumbnail_url)
            if thumbnail_image:
                channel_thumbnails.append(thumbnail_image)
        except Exception as e:
            print(f"[Error] 썸네일 로드 실패: {e}")
    
    # 브랜드 이미지 경로를 절대 경로로 변환
    brand_image_path = None
    if project.brand_image_path:
        import os
        brand_image_path = os.path.abspath(project.brand_image_path)
    
    # 실제 브랜드 서비스 사용
    result = brand_service.analyze_brand_compatibility(
        channel_id=channel_id,
        brand_name=project.company_name,
        brand_description=project.campaign_goal,
        brand_tone=project.brand_tone,
        brand_category=project.brand_categories,
        brand_image_url=brand_image_path,
        channel_description=influencer.description or "",
        channel_titles=video_titles,
        channel_thumbnails=channel_thumbnails
    )
    
    return result

@router.get("/sentiment/{project_id}/{channel_id}", response_model=SentimentScore)
def analyze_sentiment(
    project_id: str,
    channel_id: str,
    session: Session = Depends(get_db_session)
):
    """감정 분석 (실제 댓글 데이터 기반)"""
    
    from app.core.models import Video
    from app.services.roi_service import roi_service
    
    # 프로젝트 및 채널 존재 확인
    project = session.get(Project, project_id)
    influencer = session.get(Influencer, channel_id)
    
    if not project or not influencer:
        raise HTTPException(status_code=404, detail="프로젝트 또는 채널을 찾을 수 없습니다")
    
    # 해당 채널의 댓글 데이터 조회
    cursor = session.connection().execute("""
        SELECT comment_text FROM comment 
        WHERE channel_id = ? 
        ORDER BY like_count DESC 
        LIMIT 50
    """, (channel_id,))
    
    comments = [row[0] for row in cursor.fetchall()]
    
    if not comments:
        # 댓글이 없으면 기본값
        return SentimentScore(
            score=65.0,
            positive_ratio=0.60,
            negative_ratio=0.25,
            neutral_ratio=0.15,
            total_comments=0
        )
    
    # 실제 감성분석 서비스 사용
    result = roi_service.analyze_sentiment(channel_id, comments)
    
    return result

@router.get("/roi-estimate/{project_id}/{channel_id}", response_model=ROIEstimate)
def estimate_roi(
    project_id: str,
    channel_id: str,
    session: Session = Depends(get_db_session)
):
    """ROI 추정 (참여율 기반)"""
    
    from app.services.roi_service import roi_service
    
    # 프로젝트 및 채널 존재 확인
    project = session.get(Project, project_id)
    influencer = session.get(Influencer, channel_id)
    
    if not project or not influencer:
        raise HTTPException(status_code=404, detail="프로젝트 또는 채널을 찾을 수 없습니다")
    
    # ROI 추정 계산
    result = roi_service.estimate_roi(
        channel_id=channel_id,
        subscriber_count=influencer.subscriber_count or 0,
        avg_views=influencer.view_count or 1000,
        engagement_rate=influencer.engagement_rate or 1.0
    )
    
    return result

@router.get("/total-score/{project_id}/{channel_id}", response_model=TotalScore)
def get_total_score(
    project_id: str,
    channel_id: str,
    session: Session = Depends(get_db_session)
):
    """종합 점수 조회 (가중치 기반 계산)"""
    
    # 각 분석 결과 조회
    try:
        # 1. 브랜드 적합도 분석
        brand_result = analyze_brand_compatibility(project_id, channel_id, session)
        brand_score = brand_result.score
        
        # 2. 감성 분석
        sentiment_result = analyze_sentiment(project_id, channel_id, session)
        sentiment_score = sentiment_result.score
        
        # 3. ROI 추정
        roi_result = estimate_roi(project_id, channel_id, session)
        roi_score = roi_result.score
        
        # 4. 가중치 적용 계산
        from app.schemas.roi import WeightConfig
        weights = WeightConfig()  # 기본 가중치
        
        total_score = (
            brand_score * weights.brand_image_weight +
            sentiment_score * weights.sentiment_weight +
            roi_score * weights.roi_weight
        )
        
        # 등급 계산
        if total_score >= 90:
            grade = "S"
        elif total_score >= 80:
            grade = "A"
        elif total_score >= 70:
            grade = "B"
        elif total_score >= 60:
            grade = "C"
        else:
            grade = "D"
        
        # 추천 사유 생성
        if grade in ["S", "A"]:
            recommendation = "적극 추천! 높은 ROI가 예상됩니다."
        elif grade == "B":
            recommendation = "추천합니다. 양호한 성과가 예상됩니다."
        elif grade == "C":
            recommendation = "보통 수준입니다. 신중한 검토가 필요합니다."
        else:
            recommendation = "권장하지 않습니다. 다른 인플루언서를 고려해보세요."
        
        return TotalScore(
            total_score=round(total_score, 2),
            grade=grade,
            recommendation=recommendation,
            weights_used=weights
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"종합 점수 계산 중 오류 발생: {str(e)}")
