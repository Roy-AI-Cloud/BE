from fastapi import APIRouter, Depends, UploadFile, File, Form, BackgroundTasks
from sqlmodel import Session, select
from typing import List, Optional
import uuid
import json
import os
import math
from app.schemas.project import YoutuberWithROI, ProjectInfo
from app.core.models import Project, ProjectResult, Influencer
from app.core.database import engine
from app.api.deps import get_db_session
from app.services.roi_service import roi_service
from app.services.brand_service import brand_service
from app.schemas.roi import WeightConfig

router = APIRouter(prefix="/project", tags=["Project"])

def calculate_roi_score(influencer, project):
    """유튜버의 종합 ROI + 브랜드적합도 + 감성분석 점수 계산"""
    try:
        # 유튜버 썸네일 이미지 로드
        channel_thumbnails = []
        if influencer.thumbnail_url:
            try:
                from app.ml import load_image_from_url
                thumbnail_image = load_image_from_url(influencer.thumbnail_url)
                if thumbnail_image:
                    channel_thumbnails = [thumbnail_image]
            except:
                pass
        
        # 브랜드 적합도 분석 (이미지 포함)
        brand_score = brand_service.analyze_brand_compatibility(
            channel_id=influencer.channel_id,
            brand_name=project.company_name,
            brand_description=project.campaign_goal,
            brand_tone=project.brand_tone,
            brand_category=project.brand_categories,
            brand_image_path=project.brand_image_path,
            channel_description=influencer.title or "",
            channel_titles=[influencer.title or ""],
            channel_thumbnails=channel_thumbnails
        )
        
        # 감성 분석 (샘플 댓글 사용)
        sample_comments = ["좋아요", "최고예요", "유용한 정보네요"]
        sentiment_result = roi_service.analyze_sentiment(influencer.channel_id, sample_comments)
        
        # ROI 추정
        roi_result = roi_service.estimate_roi(
            influencer.channel_id,
            influencer.subscriber_count or 0,
            influencer.subscriber_count or 0,  # avg_views 대신 구독자 수 사용
            influencer.engagement_rate or 0
        )
        
        # 종합 점수 계산
        weights = WeightConfig()
        total_score_result = roi_service.calculate_total_score(
            brand_score.score,
            sentiment_result.score,
            roi_result.score,
            weights
        )
        
        return total_score_result.total_score, total_score_result.grade
        
    except Exception as e:
        # 오류 발생시 기본값 반환
        return 50.0, "C"

def analyze_project_background(project_id: str):
    """
    백그라운드에서 실행되는 프로젝트 분석 작업
    모든 인플루언서에 대해 점수를 계산하고 DB에 저장합니다.
    """
    # 백그라운드 작업은 별도의 세션을 열어야 함
    with Session(engine) as session:
        # 1. 프로젝트 조회
        project = session.get(Project, project_id)
        if not project:
            return

        # 2. 분석 대상 인플루언서 전체 조회
        influencers = session.exec(select(Influencer)).all()
        
        results_to_add = []
        
        for influencer in influencers:
            try:
                # 기존 계산 로직 재사용
                total_score, grade = calculate_roi_score(influencer, project)
                
                # 결과 객체 생성
                result = ProjectResult(
                    project_id=project_id,
                    channel_id=influencer.channel_id,
                    roi_score=total_score, # 계산된 원점수 저장
                    roi_grade=grade
                )
                results_to_add.append(result)
            except Exception as e:
                print(f"Error analyzing influencer {influencer.channel_id}: {e}")
                continue
        
        # 3. DB 일괄 저장
        if results_to_add:
            session.add_all(results_to_add)
            session.commit()

@router.post("/create", response_model=ProjectInfo)
async def create_project(
    background_tasks: BackgroundTasks,
    company_name: str = Form(...),
    brand_categories: str = Form(...),
    brand_tone: str = Form(...),
    campaign_goal: str = Form(...),
    brand_image: Optional[UploadFile] = File(None),
    session: Session = Depends(get_db_session)
):
    """프로젝트 생성 (백그라운드 분석 적용)"""
    
    project_id = str(uuid.uuid4())
    
    # 브랜드 이미지 저장
    brand_image_path = None
    if brand_image:
        os.makedirs("uploads", exist_ok=True)
        brand_image_path = f"uploads/{project_id}_{brand_image.filename}"
        
        with open(brand_image_path, "wb") as buffer:
            content = await brand_image.read()
            buffer.write(content)
    
    # 프로젝트 DB 저장
    project = Project(
        project_id=project_id,
        company_name=company_name,
        brand_categories=brand_categories,
        brand_tone=brand_tone,
        campaign_goal=campaign_goal,
        brand_image_path=brand_image_path
    )
    session.add(project)
    session.commit()
    
    # 백그라운드 분석 작업 등록
    background_tasks.add_task(analyze_project_background, project_id)
    
    return ProjectInfo(
        project_id=project_id,
        company_name=company_name,
        brand_categories=brand_categories,
        brand_tone=brand_tone,
        campaign_goal=campaign_goal,
        brand_image_path=brand_image_path,
        created_at=project.created_at,
        total_youtubers=0
    )

@router.delete("/{project_id}")
def delete_project(
    project_id: str,
    session: Session = Depends(get_db_session)
):
    """프로젝트 삭제"""
    
    # 프로젝트 존재 확인
    project = session.get(Project, project_id)
    if not project:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다")
    
    # 관련 분석 결과 삭제
    results = session.exec(
        select(ProjectResult).where(ProjectResult.project_id == project_id)
    ).all()
    for result in results:
        session.delete(result)
    
    # 브랜드 이미지 파일 삭제
    if project.brand_image_path and os.path.exists(project.brand_image_path):
        os.remove(project.brand_image_path)
    
    # 프로젝트 삭제
    session.delete(project)
    session.commit()
    
    return {"message": "프로젝트가 삭제되었습니다"}

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
            brand_image_path=project.brand_image_path,
            created_at=project.created_at,
            total_youtubers=len(youtuber_count)
        ))
    
    return result

# 상단 import에 math가 없으면 추가해주세요
import math 

@router.get("/youtubers/{project_id}", response_model=List[YoutuberWithROI])
def get_project_youtubers(
    project_id: str,
    session: Session = Depends(get_db_session)
):
    """특정 프로젝트의 유튜버 ROI 결과 조회 (상대평가 적용: S~D 등급 분포)"""
    
    # 1. 프로젝트 존재 확인
    project = session.get(Project, project_id)
    if not project:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다")
    
    # 2. DB 데이터 조회 (이미 계산된 점수 활용)
    query = select(ProjectResult, Influencer).join(
        Influencer, ProjectResult.channel_id == Influencer.channel_id
    ).where(ProjectResult.project_id == project_id)
    
    results = session.exec(query).all()
    
    # 3. 1차 리스트 생성 (DB에 저장된 점수 사용)
    raw_youtuber_list = []
    
    for result, influencer in results:
        # DB에 저장된 점수 사용 (없으면 기본값)
        current_score = result.roi_score if result.roi_score is not None else 50.0

        # YoutuberWithROI 객체 생성
        youtuber_obj = YoutuberWithROI(
            channel_id=result.channel_id,
            title=influencer.title,
            subscriber_count=influencer.subscriber_count,
            thumbnail_url=influencer.thumbnail_url,
            category=influencer.category or "미분류",
            engagement_rate=influencer.engagement_rate,
            estimated_price=influencer.estimated_price or "가격 문의",
            total_score=current_score,  # 저장된 원점수
            grade="B" # 임시 등급 (아래에서 재계산)
        )
        raw_youtuber_list.append(youtuber_obj)
    
    # ----------------------------------------------------------------
    # [핵심 수정] 여기서 49명(전체 목록)을 상대로 '상대평가' 적용
    # ----------------------------------------------------------------
    
    # 4. 원점수 기준 내림차순 정렬 (1등 -> 꼴등 줄세우기)
    sorted_youtubers = sorted(raw_youtuber_list, key=lambda x: x.total_score, reverse=True)
    
    total_count = len(sorted_youtubers)
    final_youtubers = []
    
    # 목표 점수 범위 (1등: 92점 ~ 꼴등: 53점)
    MAX_SCORE = 92.0
    MIN_SCORE = 53.0
    
    for rank, youtuber in enumerate(sorted_youtubers):
        # 백분위 계산 (0.0 = 1등, 1.0 = 꼴등)
        percentile = rank / max(1, total_count - 1)
        
        # [S-Curve 분포 공식 적용]
        # 코사인 함수를 이용해 상위/하위권 변별력을 높이고 중위권을 배치
        curve_factor = (math.cos(percentile * math.pi) + 1) / 2
        
        # 최종 점수 재할당
        final_score = MIN_SCORE + (curve_factor * (MAX_SCORE - MIN_SCORE))
        
        # 객체 업데이트
        youtuber.total_score = round(final_score, 2)
        
        youtuber.grade = roi_service._calculate_grade(final_score)
            
        final_youtubers.append(youtuber)
        
    # 5. 최종 결과 반환 (이미 점수순으로 정렬되어 있음)
    return final_youtubers