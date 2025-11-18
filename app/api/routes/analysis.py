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
    """브랜드 적합도 분석 (프로젝트 + 비디오 데이터 기반)"""
    
    from app.core.models import Video
    
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
    
    # 브랜드 카테고리 매칭 점수 계산
    brand_category = project.brand_categories.lower()
    category_score = 60.0  # 기본점수
    inf_category = (influencer.category or "").lower()
    
    if ("뷰티" in brand_category or "화장품" in brand_category) and "뷰티" in inf_category:
        category_score = 95.0
    elif ("패션" in brand_category or "의류" in brand_category) and "패션" in inf_category:
        category_score = 92.0
    elif ("식품" in brand_category or "음료" in brand_category) and "요리" in inf_category:
        category_score = 88.0
    elif ("건강" in brand_category or "의료" in brand_category) and ("뷰티" in inf_category or "운동" in inf_category):
        category_score = 85.0
    elif ("테크" in brand_category or "it" in brand_category) and "게임" in inf_category:
        category_score = 80.0
    
    # 브랜드 톤 매칭 점수
    tone_score = 70.0  # 기본점수
    if project.brand_tone == "친화적" and inf_category in ["일상", "요리"]:
        tone_score = 90.0
    elif project.brand_tone == "프리미엄" and inf_category in ["뷰티", "패션"]:
        tone_score = 85.0
    elif project.brand_tone == "럭셔리" and "패션" in inf_category:
        tone_score = 95.0
    elif project.brand_tone == "침착한" and inf_category in ["뷰티", "일상"]:
        tone_score = 80.0
    
    # 콘텐츠 품질 점수 (비디오 데이터 기반)
    content_quality = 75.0  # 기본점수
    if videos:
        avg_views = sum(v.view_count or 0 for v in videos) / len(videos)
        avg_likes = sum(v.like_count or 0 for v in videos) / len(videos)
        
        if avg_views > 50000:
            content_quality += 10
        if avg_likes > 1000:
            content_quality += 5
        
        content_quality = min(content_quality, 95.0)
    
    # 오디언스 매칭 (구독자 수 기반)
    audience_score = 70.0
    if influencer.subscriber_count:
        if 50000 <= influencer.subscriber_count <= 500000:
            audience_score = 90.0
        elif influencer.subscriber_count > 500000:
            audience_score = 85.0
        elif influencer.subscriber_count > 10000:
            audience_score = 80.0
    
    # 브랜드 안전성 (참여율 기반)
    brand_safety = 85.0
    if influencer.engagement_rate:
        if influencer.engagement_rate > 5.0:
            brand_safety = 95.0
        elif influencer.engagement_rate > 2.0:
            brand_safety = 90.0
    
    # 전체 점수 계산
    overall_score = (category_score + tone_score + content_quality + audience_score + brand_safety) / 5
    
    return BrandImageScore(
        score=round(overall_score, 1),  # 추가
        details={  # 추가
            "category_match": category_score,
            "tone_match": tone_score,
            "audience_match": audience_score,
            "content_quality": content_quality,
            "brand_safety": brand_safety
        },
        overall_score=round(overall_score, 1),
        category_match=category_score,
        tone_match=tone_score,
        audience_match=audience_score,
        content_quality=content_quality,
        brand_safety=brand_safety
    )

@router.get("/sentiment/{project_id}/{channel_id}", response_model=SentimentScore)
def analyze_sentiment(
    project_id: str,
    channel_id: str,
    session: Session = Depends(get_db_session)
):
    """감정 분석 (샘플 비디오 데이터 기반)"""
    
    from app.core.models import Video
    
    # 프로젝트 및 채널 존재 확인
    project = session.get(Project, project_id)
    influencer = session.get(Influencer, channel_id)
    
    if not project or not influencer:
        raise HTTPException(status_code=404, detail="프로젝트 또는 채널을 찾을 수 없습니다")
    
    # 해당 채널의 비디오 데이터 조회
    videos = session.exec(
        select(Video).where(Video.channel_id == channel_id)
    ).all()
    
    if not videos:
        # 비디오가 없으면 기본값
        return SentimentScore(
            score=65.0,  # 추가
            positive_ratio=0.60,
            negative_ratio=0.25,
            neutral_ratio=0.15,
            total_comments=0  # comment_count -> total_comments
        )
    
    # 비디오 데이터 기반 감성분석
    total_comments = sum(video.comment_count or 0 for video in videos)
    total_likes = sum(video.like_count or 0 for video in videos)
    total_views = sum(video.view_count or 0 for video in videos)
    
    # 참여율 기반 감성 점수 계산
    if total_views > 0:
        engagement_rate = (total_likes + total_comments) / total_views
        
        # 참여율이 높을수록 긍정적
        if engagement_rate > 0.05:  # 5% 이상
            positive_ratio = 0.80
            negative_ratio = 0.10
            overall_sentiment = 90.0
        elif engagement_rate > 0.03:  # 3% 이상
            positive_ratio = 0.75
            negative_ratio = 0.15
            overall_sentiment = 80.0
        elif engagement_rate > 0.01:  # 1% 이상
            positive_ratio = 0.65
            negative_ratio = 0.20
            overall_sentiment = 70.0
        else:
            positive_ratio = 0.50
            negative_ratio = 0.35
            overall_sentiment = 55.0
    else:
        positive_ratio = 0.60
        negative_ratio = 0.25
        overall_sentiment = 65.0
    
    neutral_ratio = 1.0 - positive_ratio - negative_ratio
    
    return SentimentScore(
        score=overall_sentiment,  # 추가
        positive_ratio=positive_ratio,
        negative_ratio=negative_ratio,
        neutral_ratio=neutral_ratio,
        total_comments=total_comments  # comment_count -> total_comments
    )

@router.get("/roi-estimate/{project_id}/{channel_id}", response_model=ROIEstimate)
def estimate_roi(
    project_id: str,
    channel_id: str,
    session: Session = Depends(get_db_session)
):
    """ROI 추정 (비디오 데이터 기반)"""
    
    from app.core.models import Video
    
    # 프로젝트 및 채널 정보 조회
    project = session.get(Project, project_id)
    influencer = session.get(Influencer, channel_id)
    
    if not project or not influencer:
        raise HTTPException(status_code=404, detail="프로젝트 또는 채널을 찾을 수 없습니다")
    
    # ROI 결과 조회
    roi_result = session.exec(
        select(ProjectResult).where(
            ProjectResult.project_id == project_id,
            ProjectResult.channel_id == channel_id
        )
    ).first()
    
    if not roi_result:
        raise HTTPException(status_code=404, detail="분석 결과를 찾을 수 없습니다")
    
    # 비디오 데이터 기반 예상 성과 계산
    videos = session.exec(
        select(Video).where(Video.channel_id == channel_id)
    ).all()
    
    if videos:
        # 평균 조회수/참여수 계산
        avg_views = sum(v.view_count or 0 for v in videos) / len(videos)
        avg_likes = sum(v.like_count or 0 for v in videos) / len(videos)
        avg_comments = sum(v.comment_count or 0 for v in videos) / len(videos)
        
        # 예상 조회수 (평균의 80-120% 범위)
        estimated_views = int(avg_views * 0.9)
        estimated_engagement = int((avg_likes + avg_comments) * 0.9)
    else:
        # 구독자 수 기반 추정
        estimated_views = int((influencer.subscriber_count or 10000) * 0.1)
        estimated_engagement = int((influencer.subscriber_count or 10000) * 0.03)
    
    # 예상 비용 계산 (구독자 수 기반)
    if influencer.subscriber_count:
        if influencer.subscriber_count > 1000000:
            estimated_cost = 8000000
        elif influencer.subscriber_count > 500000:
            estimated_cost = 5000000
        elif influencer.subscriber_count > 100000:
            estimated_cost = 3000000
        elif influencer.subscriber_count > 50000:
            estimated_cost = 2000000
        else:
            estimated_cost = 1000000
    else:
        estimated_cost = 1500000
    
    # 손익분기점 계산 (조회수당 수익 10원 가정)
    break_even_views = estimated_cost / 10
    
    # CPM 계산 (1000회 노출당 비용)
    cpm = (estimated_cost / estimated_views) * 1000 if estimated_views > 0 else 1500.0
    
    return ROIEstimate(
        score=roi_result.roi_score,  # 추가
        estimated_views=estimated_views,
        estimated_engagement=estimated_engagement,
        estimated_cost=str(estimated_cost),  # 문자열로 변환
        cpm=round(cpm, 2),  # 추가
        roi_percentage=roi_result.roi_score,
        break_even_views=int(break_even_views)
    )

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
        brand_score = brand_result.score  # overall_score -> score
        
        # 2. 감성 분석
        sentiment_result = analyze_sentiment(project_id, channel_id, session)
        sentiment_score = sentiment_result.score  # overall_sentiment -> score
        
        # 3. ROI 추정
        roi_result = estimate_roi(project_id, channel_id, session)
        roi_score = roi_result.score  # roi_percentage -> score
        
        # 4. 가중치 적용 계산
        from app.schemas.roi import WeightConfig
        weights = WeightConfig()  # 기본 가중치
        
        total_score = (
            brand_score * weights.brand_image_weight +  # brand_weight -> brand_image_weight
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
            total_score=round(total_score, 1),
            grade=grade,
            recommendation=recommendation,
            weights_used=weights
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"종합 점수 계산 오류: {str(e)}")
