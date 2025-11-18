from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlmodel import Session, select
from typing import List, Optional
import uuid
import random
import json
import os

from app.schemas.project import YoutuberWithROI, ProjectInfo
from app.core.models import Project, ProjectResult, Influencer
from app.api.deps import get_db_session

router = APIRouter(prefix="/project", tags=["Project"])

def calculate_roi_score(influencer: Influencer, project: Project) -> tuple[float, str]:
    """ROI 점수 및 등급 계산 (문자열 기반)"""
    
    score = 0.0
    brand_category = project.brand_categories.lower()  # 소문자로 변환
    
    # 구독자 수 (25%)
    if influencer.subscriber_count:
        if 50000 <= influencer.subscriber_count <= 500000:
            score += 25
        elif influencer.subscriber_count > 500000:
            score += 20
        else:
            score += 15
    
    # 참여율 (35%)
    if influencer.engagement_rate:
        if influencer.engagement_rate >= 3.0:
            score += 35
        elif influencer.engagement_rate >= 1.5:
            score += 25
        else:
            score += 15
    
    # 카테고리 매칭 (30%) - 문자열 포함 검사
    category_match = 10  # 기본점수
    inf_category = (influencer.category or "").lower()
    
    if ("뷰티" in brand_category or "화장품" in brand_category) and "뷰티" in inf_category:
        category_match = 30
    elif ("패션" in brand_category or "의류" in brand_category) and "패션" in inf_category:
        category_match = 30
    elif ("식품" in brand_category or "음료" in brand_category) and "요리" in inf_category:
        category_match = 25
    elif ("건강" in brand_category or "의료" in brand_category) and ("뷰티" in inf_category or "운동" in inf_category):
        category_match = 25
    elif ("테크" in brand_category or "it" in brand_category) and "게임" in inf_category:
        category_match = 20
    
    score += category_match
    
    # 브랜드 톤 매칭 (10%)
    tone_score = 5  # 기본점수
    if project.brand_tone == "친화적" and inf_category in ["일상", "요리", "여행"]:
        tone_score = 10
    elif project.brand_tone == "프리미엄" and inf_category in ["뷰티", "패션"]:
        tone_score = 10
    elif project.brand_tone == "럭셔리" and "패션" in inf_category:
        tone_score = 10
    elif project.brand_tone == "침착한" and inf_category in ["뷰티", "일상"]:
        tone_score = 8
    
    score += tone_score
    
    # 등급 계산
    if score >= 90:
        grade = "S"
    elif score >= 80:
        grade = "A"
    elif score >= 70:
        grade = "B"
    elif score >= 60:
        grade = "C"
    else:
        grade = "D"
    
    return round(score, 1), grade

@router.post("/create", response_model=List[YoutuberWithROI])
async def create_project(
    company_name: str = Form(...),
    brand_categories: str = Form(...),  # 단순 문자열로 받기
    brand_tone: str = Form(...),
    campaign_goal: str = Form(...),
    brand_image: Optional[UploadFile] = File(None),
    session: Session = Depends(get_db_session)
):
    """새 프로젝트 생성 및 전체 유튜버 ROI 분석"""
    
    project_id = str(uuid.uuid4())
    
    # 브랜드 이미지 저장
    brand_image_path = None
    if brand_image:
        os.makedirs("uploads", exist_ok=True)
        brand_image_path = f"uploads/{project_id}_{brand_image.filename}"
        with open(brand_image_path, "wb") as f:
            content = await brand_image.read()
            f.write(content)
    
    # 프로젝트 생성
    project = Project(
        project_id=project_id,
        company_name=company_name,
        brand_categories=brand_categories,  # 문자열 그대로 저장
        brand_tone=brand_tone,
        campaign_goal=campaign_goal,
        brand_image_path=brand_image_path
    )
    session.add(project)
    
    # 전체 유튜버에 대해 ROI 분석
    influencers = session.exec(select(Influencer)).all()
    results = []
    
    for inf in influencers:
        roi_score, roi_grade = calculate_roi_score(inf, project)
        
        # DB에 저장
        result = ProjectResult(
            project_id=project_id,
            channel_id=inf.channel_id,
            roi_score=roi_score,
            roi_grade=roi_grade
        )
        session.add(result)
        
        # 응답 데이터 준비
        results.append(YoutuberWithROI(
            channel_id=inf.channel_id,
            title=inf.title,
            subscriber_count=inf.subscriber_count,
            thumbnail_url=inf.thumbnail_url,
            category=inf.category or "미분류",
            engagement_rate=inf.engagement_rate,
            estimated_price=inf.estimated_price or "가격 문의",
            total_score=roi_score,  # 필드명 변경
            grade=roi_grade  # 필드명 변경
        ))
    
    session.commit()
    
    # ROI 점수 순으로 정렬해서 반환
    return sorted(results, key=lambda x: x.total_score, reverse=True)

@router.get("/list", response_model=List[ProjectInfo])
def get_project_list(
    session: Session = Depends(get_db_session)
):
    """생성된 프로젝트 목록 조회"""
    
    projects = session.exec(select(Project).order_by(Project.created_at.desc())).all()
    
    result = []
    for project in projects:
        # 각 프로젝트별 분석된 유튜버 수 계산
        youtuber_count = session.exec(
            select(ProjectResult).where(ProjectResult.project_id == project.project_id)
        ).all()
        
        result.append(ProjectInfo(
            project_id=project.project_id,
            company_name=project.company_name,
            brand_categories=project.brand_categories,
            brand_tone=project.brand_tone,
            campaign_goal=project.campaign_goal,
            created_at=project.created_at,
            total_youtubers=len(youtuber_count)
        ))
    
    return result

@router.get("/youtubers/{project_id}", response_model=List[YoutuberWithROI])
def get_project_youtubers(
    project_id: str,
    session: Session = Depends(get_db_session)
):
    """특정 프로젝트의 유튜버 ROI 결과 조회 (종합점수 기반)"""
    
    # 프로젝트 존재 확인
    project = session.get(Project, project_id)
    if not project:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다")
    
    # 프로젝트 결과와 인플루언서 정보 조회
    query = select(ProjectResult, Influencer).join(
        Influencer, ProjectResult.channel_id == Influencer.channel_id
    ).where(ProjectResult.project_id == project_id)
    
    results = session.exec(query).all()
    
    youtubers_with_total_score = []
    
    for result, influencer in results:
        try:
            # 각 유튜버별 종합점수 계산
            from app.api.routes.analysis import get_total_score
            total_score_result = get_total_score(project_id, influencer.channel_id, session)
            
            youtubers_with_total_score.append(YoutuberWithROI(
                channel_id=result.channel_id,
                title=influencer.title,
                subscriber_count=influencer.subscriber_count,
                thumbnail_url=influencer.thumbnail_url,
                category=influencer.category or "미분류",
                engagement_rate=influencer.engagement_rate,
                estimated_price=influencer.estimated_price or "가격 문의",
                total_score=total_score_result.total_score,  # 필드명 변경
                grade=total_score_result.grade  # 필드명 변경
            ))
            
        except Exception as e:
            # 종합점수 계산 실패시 기존 roi_score 사용
            youtubers_with_total_score.append(YoutuberWithROI(
                channel_id=result.channel_id,
                title=influencer.title,
                subscriber_count=influencer.subscriber_count,
                thumbnail_url=influencer.thumbnail_url,
                category=influencer.category or "미분류",
                engagement_rate=influencer.engagement_rate,
                estimated_price=influencer.estimated_price or "가격 문의",
                total_score=result.roi_score,  # 필드명 변경
                grade=result.roi_grade  # 필드명 변경
            ))
    
    # total_score 기준으로 정렬
    return sorted(youtubers_with_total_score, key=lambda x: x.total_score, reverse=True)

@router.get("/youtubers/{project_id}", response_model=List[YoutuberWithROI])
def get_project_youtubers(
    project_id: str,
    session: Session = Depends(get_db_session)
):
    """프로젝트별 유튜버 ROI 결과 조회"""
    
    # 프로젝트 결과와 인플루언서 정보 조인
    query = """
    SELECT i.*, pr.roi_score, pr.roi_grade 
    FROM influencer i 
    JOIN projectresult pr ON i.channel_id = pr.channel_id 
    WHERE pr.project_id = ?
    ORDER BY pr.roi_score DESC
    """
    
    results = session.exec(query, [project_id]).all()
    
    return [
        YoutuberWithROI(
            channel_id=row.channel_id,
            title=row.title,
            subscriber_count=row.subscriber_count,
            thumbnail_url=row.thumbnail_url,
            category=row.category or "미분류",
            engagement_rate=row.engagement_rate,
            estimated_price=row.estimated_price or "가격 문의",
            roi_score=row.roi_score,
            roi_grade=row.roi_grade
        )
        for row in results
    ]
