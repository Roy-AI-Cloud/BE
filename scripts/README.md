# Scripts

데이터 수집 및 초기 설정을 위한 스크립트들

## 📁 파일 목록

### 초기 설정
- `update_schema.py` - DB 스키마 업데이트 (썸네일, 댓글 테이블 추가)

### 데이터 수집
- `crawler.py` - 유튜버 기본 정보 수집 (YouTube API)
- `collect_youtube_data.py` - 실제 비디오/댓글 데이터 수집 (YouTube API)

### 샘플 데이터 생성
- `create_sample_videos.py` - 샘플 비디오 데이터 생성
- `add_sample_thumbnails.py` - 샘플 썸네일 URL 추가
- `add_sample_comments.py` - 현실적인 샘플 댓글 생성

## 🚀 실행 순서

### 1. 초기 설정 (최초 1회)
```bash
# DB 스키마 업데이트
python scripts/update_schema.py

# 유튜버 기본 정보 수집
python scripts/crawler.py

# 샘플 비디오 데이터 생성
python scripts/create_sample_videos.py
```

### 2. 추가 데이터 생성
```bash
# 썸네일 URL 추가
python scripts/add_sample_thumbnails.py

# 댓글 데이터 생성
python scripts/add_sample_comments.py
```

### 3. 실제 데이터 수집 (YouTube API 할당량 필요)
```bash
# 실제 YouTube 데이터 수집
python scripts/collect_youtube_data.py
```

## ⚠️ 주의사항

- YouTube API 키가 `.env` 파일에 설정되어 있어야 함
- `collect_youtube_data.py`는 API 할당량을 많이 사용하므로 주의
- 샘플 데이터 스크립트들은 API 없이도 실행 가능
