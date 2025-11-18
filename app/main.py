from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.core import create_db_and_tables
from app.api import api_router

def create_application() -> FastAPI:
    """FastAPI 애플리케이션 생성 및 설정"""
    
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description=settings.DESCRIPTION,
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json"
    )

    # CORS 설정
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 이벤트 핸들러
    @app.on_event("startup")
    async def startup_event():
        create_db_and_tables()
        print("✅ Database initialized")
        print(f"🚀 {settings.PROJECT_NAME} is ready!")

    # 루트 엔드포인트
    @app.get("/")
    def root():
        return {
            "message": f"{settings.PROJECT_NAME} v{settings.VERSION}",
            "docs": "/docs",
            "api": settings.API_V1_STR,
            "endpoints": {
                "home": f"{settings.API_V1_STR}/home",
                "youtuber": f"{settings.API_V1_STR}/youtuber",
                "analysis": f"{settings.API_V1_STR}/analysis",
                "compare": f"{settings.API_V1_STR}/compare"
            }
        }

    # API 라우터 등록
    app.include_router(api_router, prefix=settings.API_V1_STR)

    return app

app = create_application()
