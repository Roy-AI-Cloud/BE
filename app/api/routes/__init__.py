from fastapi import APIRouter
from .home import router as home_router
from .youtuber import router as youtuber_router
from .analysis import router as analysis_router
from .compare import router as compare_router
from .project import router as project_router

api_router = APIRouter()

# 각 페이지별 라우터 등록
api_router.include_router(home_router)
api_router.include_router(youtuber_router)
api_router.include_router(analysis_router)
api_router.include_router(compare_router)
api_router.include_router(project_router)
