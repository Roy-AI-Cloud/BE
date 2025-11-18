"""
비교 페이지 관련 API (프로젝트 기반)
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from typing import List, Dict
from pydantic import BaseModel
from app.schemas.roi import WeightConfig
from app.core.models import Project, Influencer
from app.api.deps import get_db_session

router = APIRouter(prefix="/compare", tags=["Compare"])

class ChannelCompareRequest(BaseModel):
    project_id: str
    channel_ids: List[str]

class WeightCompareRequest(BaseModel):
    project_id: str
    channel_id: str
    weight_configs: List[WeightConfig]

@router.post("/channels")
def compare_channels(
    req: ChannelCompareRequest,
    session: Session = Depends(get_db_session)
):
    """여러 채널 비교 분석 (프로젝트 기반)"""
    
    # 프로젝트 존재 확인
    project = session.get(Project, req.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다")
    
    results = []
    
    for channel_id in req.channel_ids:
        try:
            # 각 채널별 종합 분석 결과 조회
            from app.api.routes.analysis import (
                analyze_brand_compatibility, 
                analyze_sentiment, 
                estimate_roi, 
                get_total_score
            )
            
            # 개별 분석 결과
            brand_result = analyze_brand_compatibility(req.project_id, channel_id, session)
            sentiment_result = analyze_sentiment(req.project_id, channel_id, session)
            roi_result = estimate_roi(req.project_id, channel_id, session)
            total_result = get_total_score(req.project_id, channel_id, session)
            
            # 채널 정보
            influencer = session.get(Influencer, channel_id)
            
            channel_result = {
                "channel_id": channel_id,
                "channel_name": influencer.title if influencer else "Unknown",
                "subscriber_count": influencer.subscriber_count if influencer else 0,
                "brand_score": brand_result.score,
                "sentiment_score": sentiment_result.score,
                "roi_score": roi_result.score,
                "total_score": total_result.total_score,
                "grade": total_result.grade,
                "recommendation": total_result.recommendation
            }
            results.append(channel_result)
            
        except Exception as e:
            # 분석 실패한 채널은 제외
            continue
    
    if not results:
        raise HTTPException(status_code=404, detail="분석 가능한 채널이 없습니다")
    
    return {
        "project_id": req.project_id,
        "comparison_results": results,
        "best_channel": max(results, key=lambda x: x["total_score"]),
        "analysis_criteria": {
            "brand_weight": 0.4,
            "sentiment_weight": 0.3,
            "roi_weight": 0.3
        }
    }

@router.post("/weights")
def compare_weights(
    req: WeightCompareRequest,
    session: Session = Depends(get_db_session)
):
    """가중치별 비교 분석 (프로젝트 기반)"""
    
    # 프로젝트 존재 확인
    project = session.get(Project, req.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다")
    
    # 채널 존재 확인
    influencer = session.get(Influencer, req.channel_id)
    if not influencer:
        raise HTTPException(status_code=404, detail="채널을 찾을 수 없습니다")
    
    results = []
    
    for i, weights in enumerate(req.weight_configs):
        try:
            # 개별 분석 점수 조회
            from app.api.routes.analysis import (
                analyze_brand_compatibility, 
                analyze_sentiment, 
                estimate_roi
            )
            
            brand_result = analyze_brand_compatibility(req.project_id, req.channel_id, session)
            sentiment_result = analyze_sentiment(req.project_id, req.channel_id, session)
            roi_result = estimate_roi(req.project_id, req.channel_id, session)
            
            # 가중치 적용 계산
            total_score = (
                brand_result.score * weights.brand_image_weight +
                sentiment_result.score * weights.sentiment_weight +
                roi_result.score * weights.roi_weight
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
            
            weight_result = {
                "weight_config": {
                    "name": f"Config {i+1}",
                    "brand_weight": weights.brand_image_weight,
                    "sentiment_weight": weights.sentiment_weight,
                    "roi_weight": weights.roi_weight
                },
                "total_score": round(total_score, 1),
                "grade": grade,
                "score_breakdown": {
                    "brand_score": brand_result.score,
                    "sentiment_score": sentiment_result.score,
                    "roi_score": roi_result.score
                }
            }
            results.append(weight_result)
            
        except Exception as e:
            continue
    
    if not results:
        raise HTTPException(status_code=500, detail="가중치 분석에 실패했습니다")
    
    return {
        "project_id": req.project_id,
        "channel_id": req.channel_id,
        "channel_name": influencer.title,
        "weight_comparison": results,
        "optimal_weights": max(results, key=lambda x: x["total_score"])["weight_config"]
    }
