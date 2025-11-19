# InfluROI YouTube API

유튜버 마케팅 ROI 분석 및 브랜드 적합도 API

## 📋 개요

InfluROI는 유튜버와 브랜드 간의 마케팅 협업에서 ROI(투자 수익률)를 분석하고 예측하는 FastAPI 기반 웹 서비스입니다.

## 🚀 주요 기능

- **프로젝트 기반 분석**: 브랜드 정보를 프로젝트로 저장하여 일관된 분석
- **종합 점수 계산**: 브랜드 적합도(40%) + 감성분석(30%) + ROI 추정(30%)
- **유튜버 데이터 수집**: YouTube API를 통한 채널 및 비디오 데이터 수집
- **실시간 분석**: 실제 YouTube API 데이터 기반 분석 수행
- **비교 분석**: 여러 유튜버 또는 가중치 비교
- **자동 등급 산정**: S, A, B, C, D 등급 자동 계산

## 🏗️ 프로젝트 구조

```
infloi/
├── app/
│   ├── api/                    # API 엔드포인트
│   │   ├── routes/
│   │   │   ├── home.py         # 홈화면 API (유튜버 목록, 정렬)
│   │   │   ├── project.py      # 프로젝트 관리 API
│   │   │   ├── analysis.py     # 분석 API (브랜드적합도, 감성분석, ROI)
│   │   │   ├── compare.py      # 비교분석 API
│   │   │   └── youtuber.py     # 유튜버 상세 API
│   │   └── deps.py             # 의존성 주입
│   ├── core/                   # 핵심 모듈
│   │   ├── database.py         # 데이터베이스 설정
│   │   └── models.py           # SQLModel 데이터 모델
│   ├── schemas/                # Pydantic 스키마
│   │   ├── project.py          # 프로젝트 관련 스키마
│   │   ├── roi.py              # ROI 분석 스키마
│   │   └── youtube.py          # YouTube 데이터 스키마
│   ├── services/               # 비즈니스 로직
│   │   ├── brand_service.py    # 브랜드 분석 서비스
│   │   ├── roi_service.py      # ROI 계산 서비스
│   │   └── youtube_service.py  # YouTube 데이터 서비스
│   ├── utils/                  # 유틸리티
│   │   └── youtube_utils.py    # YouTube API 유틸
│   ├── config/                 # 설정 파일
│   │   └── settings.py         # 앱 설정
│   └── main.py                 # FastAPI 앱
├── db/                         # SQLite 데이터베이스
│   └── influencer.db           # 유튜버 및 프로젝트 데이터
├── uploads/                    # 업로드된 브랜드 이미지
├── crawler.py                  # 유튜버 데이터 수집 크롤러
├── create_sample_videos.py     # 샘플 비디오 데이터 생성
├── run.py                      # 서버 실행 파일
├── requirements.txt            # 의존성 목록
└── .env                        # 환경 변수
```

## 🛠️ 기술 스택

- **Backend**: FastAPI, SQLModel, SQLite
- **AI/ML**: PyTorch, Transformers, KoBERT, CLIP
- **API**: YouTube Data API v3
- **Database**: SQLite (개발용)

## 📦 설치 및 실행

### 1. 환경 설정

```bash
# 프로젝트 클론
git clone <repository-url>
cd infloi

# 가상환경 생성 (권장)
python -m venv venv

# 가상환경 활성화
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 2. 환경 변수 설정

`.env` 파일 생성:
```env
# API 설정
API_V1_STR=/api
PROJECT_NAME=InfluROI YouTube API
VERSION=2.0.0

# 데이터베이스
DATABASE_URL=sqlite:///./db/influencer.db

# YouTube API (필수)
YOUTUBE_API_KEY=your_youtube_api_key_here

# AI 모델 설정
CLIP_MODEL_NAME=openai/clip-vit-base-patch32
SBERT_MODEL=sentence-transformers/xlm-r-100langs-bert-base-nli-stsb-mean-tokens
KOBERT_MODEL=monologg/kobert
```

### 3. 데이터베이스 초기화

```bash
# 데이터베이스 테이블 생성
python -c "from app.core.database import create_db_and_tables; create_db_and_tables()"

# 스키마 업데이트 (썸네일, 댓글 테이블 추가)
python scripts/update_schema.py

# 유튜버 데이터 수집 (YouTube API 할당량 필요)
python scripts/crawler.py

# 샘플 비디오 데이터 생성
python scripts/create_sample_videos.py

# 썸네일 및 댓글 데이터 추가
python scripts/add_sample_thumbnails.py
python scripts/add_sample_comments.py
```

**참고**: 자세한 스크립트 사용법은 [`scripts/README.md`](./scripts/README.md)를 참조하세요.

### 4. 서버 실행

```bash
# 개발 서버 실행
python run.py

# 또는 직접 uvicorn 실행
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 5. 접속 확인

- **서버**: http://localhost:8000
- **API 문서**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📚 주요 API

### 프로젝트 관리
- `POST /api/project/create` - 새 프로젝트 생성 및 전체 유튜버 ROI 분석
- `GET /api/project/list` - 생성된 프로젝트 목록 조회
- `GET /api/project/youtubers/{project_id}` - 프로젝트별 유튜버 결과 조회

### 홈화면
- `GET /api/home/youtubers` - 유튜버 목록 조회
- `GET /api/home/youtubers/sorted?sort_by=followers|engagement|price` - 정렬된 유튜버 목록

### 분석 (프로젝트 기반)
- `GET /api/analysis/brand-match/{project_id}/{channel_id}` - 브랜드 적합도 분석
- `GET /api/analysis/sentiment/{project_id}/{channel_id}` - 감성 분석
- `GET /api/analysis/roi-estimate/{project_id}/{channel_id}` - ROI 추정
- `GET /api/analysis/total-score/{project_id}/{channel_id}` - 종합 점수 조회

### 비교 분석
- `POST /api/compare/channels` - 여러 채널 비교 분석
- `POST /api/compare/weights` - 가중치별 비교 분석

### 유튜버 상세
- `GET /api/youtuber/{channel_id}/profile` - 유튜버 프로필
- `GET /api/youtuber/{channel_id}/videos` - 유튜버 영상 목록
- `GET /api/youtuber/{channel_id}/stats` - 유튜버 통계

## 🔄 사용 플로우

1. **프로젝트 생성**: 브랜드 정보 입력 → 전체 유튜버 ROI 분석 실행
2. **결과 확인**: 종합점수 기준으로 정렬된 유튜버 목록 확인
3. **상세 분석**: 특정 유튜버 선택 → 브랜드적합도, 감성분석, ROI 상세 확인
4. **비교 분석**: 여러 유튜버 비교 또는 가중치 변경 분석

## 🤖 분석 로직

### 종합 점수 계산
```
total_score = 브랜드적합도(40%) + 감성분석(30%) + ROI추정(30%)
```

### 등급 기준
- **S등급**: 90점 이상 (최우수)
- **A등급**: 80-89점 (우수)
- **B등급**: 70-79점 (양호)
- **C등급**: 60-69점 (보통)
- **D등급**: 60점 미만 (부족)

### 브랜드 적합도 (40%)
- 카테고리 매칭 (뷰티↔뷰티, 패션↔패션 등)
- 브랜드 톤 매칭 (친화적, 프리미엄, 럭셔리)
- 콘텐츠 품질 (조회수, 좋아요 기반)
- 오디언스 매칭 (구독자 수 적정성)
- 브랜드 안전성 (참여율 기반)

### 감성 분석 (30%)
- 비디오 참여율 기반 감성 점수
- 긍정/부정/중립 비율 계산
- 댓글 수 및 반응 분석

### ROI 추정 (30%)
- 과거 비디오 성과 기반 예상 조회수
- 구독자 수별 차등 협찬비 계산
- CPM 및 손익분기점 계산

## 🗃️ 데이터베이스 구조

### 주요 테이블
- **Influencer**: 유튜버 기본 정보 (49명)
- **Video**: 유튜버별 샘플 비디오 데이터 (3-5개씩)
- **Project**: 브랜드 프로젝트 정보
- **ProjectResult**: 프로젝트별 유튜버 ROI 결과

## ⚠️ 주의사항

- YouTube API 할당량 제한으로 실시간 데이터 수집에 제약
- 현재 샘플 비디오 데이터 기반으로 분석 수행
- 실제 서비스 배포 시 PostgreSQL 등 운영 DB 권장
