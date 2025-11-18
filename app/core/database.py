from sqlmodel import SQLModel, create_engine, Session
from pathlib import Path
from app.config import settings

# 데이터베이스 파일 경로 설정
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DB_DIR = ROOT_DIR / "db"
DB_DIR.mkdir(exist_ok=True)

# 엔진 생성
engine = create_engine(
    settings.DATABASE_URL,
    echo=False,  # 프로덕션에서는 False
    connect_args={"check_same_thread": False}
)

def create_db_and_tables():
    """데이터베이스와 테이블 생성"""
    SQLModel.metadata.create_all(engine)

def get_session():
    """데이터베이스 세션 의존성"""
    with Session(engine) as session:
        yield session
