from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # API 설정
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "InfluROI YouTube API"
    VERSION: str = "2.0.0"
    DESCRIPTION: str = "유튜버 마케팅 ROI 분석 및 시뮬레이터 API"
    
    # CORS 설정
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    # 데이터베이스 설정
    DATABASE_URL: str = "sqlite:///./db/influencer.db"
    
    # AI 모델 설정
    CLIP_MODEL_NAME: str = "openai/clip-vit-base-patch32"
    SBERT_MODEL: str = "sentence-transformers/xlm-r-100langs-bert-base-nli-stsb-mean-tokens"
    KOBERT_MODEL: str = "monologg/kobert"
    
    # YouTube API 설정
    YOUTUBE_API_KEY: str = ""
    
    class Config:
        env_file = ".env"

settings = Settings()
