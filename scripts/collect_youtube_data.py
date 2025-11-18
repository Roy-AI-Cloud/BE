"""
YouTube API를 통한 실제 데이터 수집
- 비디오 썸네일 URL
- 비디오 댓글
"""
import sqlite3
import httpx
from typing import List, Dict
from datetime import datetime
from app.config.settings import settings

API_KEY = settings.YOUTUBE_API_KEY
YOUTUBE_BASE_URL = "https://www.googleapis.com/youtube/v3"

def get_channel_videos(channel_id: str, max_results: int = 3) -> List[Dict]:
    """채널의 최근 비디오 가져오기"""
    try:
        params = {
            "part": "snippet",
            "channelId": channel_id,
            "maxResults": max_results,
            "order": "date",
            "type": "video",
            "key": API_KEY
        }
        
        response = httpx.get(f"{YOUTUBE_BASE_URL}/search", params=params)
        response.raise_for_status()
        data = response.json()
        
        return data.get('items', [])
    except Exception as e:
        print(f"비디오 검색 오류: {e}")
        return []

def get_video_comments(video_id: str, max_results: int = 20) -> List[Dict]:
    """비디오 댓글 가져오기"""
    try:
        params = {
            "part": "snippet",
            "videoId": video_id,
            "maxResults": max_results,
            "order": "relevance",
            "key": API_KEY
        }
        
        response = httpx.get(f"{YOUTUBE_BASE_URL}/commentThreads", params=params)
        response.raise_for_status()
        data = response.json()
        
        return data.get('items', [])
    except Exception as e:
        print(f"댓글 수집 오류: {e}")
        return []

def collect_video_thumbnails_and_comments():
    """각 유튜버의 비디오 썸네일과 댓글 수집"""
    
    if not API_KEY:
        print("❌ YouTube API 키가 설정되지 않았습니다")
        return
    
    # DB 연결
    conn = sqlite3.connect('db/influencer.db')
    cursor = conn.cursor()
    
    # 모든 인플루언서 조회 (처음 5명만 테스트)
    cursor.execute("SELECT channel_id, title FROM influencer LIMIT 5")
    influencers = cursor.fetchall()
    
    print(f"📊 {len(influencers)}명의 인플루언서 데이터 수집 시작...")
    
    for channel_id, title in influencers:
        print(f"\n🎯 {title} ({channel_id}) 처리 중...")
        
        try:
            # 1. 최근 비디오 3개 가져오기
            videos = get_channel_videos(channel_id, max_results=3)
            
            if not videos:
                print(f"⚠️ {title}: 비디오를 찾을 수 없습니다")
                continue
            
            for video in videos:
                video_id = video['id']['videoId']
                video_title = video['snippet']['title']
                thumbnail_url = video['snippet']['thumbnails'].get('medium', {}).get('url', '')
                
                # 2. 기존 비디오 데이터 확인 후 업데이트
                cursor.execute("SELECT video_id FROM video WHERE video_id = ?", (video_id,))
                existing = cursor.fetchone()
                
                if existing:
                    # 기존 비디오에 썸네일 URL 업데이트
                    cursor.execute("""
                        UPDATE video 
                        SET thumbnail_url = ? 
                        WHERE video_id = ?
                    """, (thumbnail_url, video_id))
                else:
                    # 새 비디오 추가
                    cursor.execute("""
                        INSERT INTO video (video_id, video_title, channel_id, thumbnail_url)
                        VALUES (?, ?, ?, ?)
                    """, (video_id, video_title, channel_id, thumbnail_url))
                
                print(f"  📸 썸네일 업데이트: {video_title[:30]}...")
                
                # 3. 댓글 수집 (최대 10개로 제한)
                comments = get_video_comments(video_id, max_results=10)
                
                comment_count = 0
                for comment in comments:
                    comment_id = comment['id']
                    comment_text = comment['snippet']['topLevelComment']['snippet']['textDisplay']
                    like_count = comment['snippet']['topLevelComment']['snippet']['likeCount']
                    published_at = comment['snippet']['topLevelComment']['snippet']['publishedAt']
                    author_name = comment['snippet']['topLevelComment']['snippet']['authorDisplayName']
                    
                    # 댓글 저장 (중복 방지)
                    cursor.execute("""
                        INSERT OR IGNORE INTO comment 
                        (comment_id, video_id, channel_id, comment_text, like_count, published_at, author_name)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (comment_id, video_id, channel_id, comment_text, like_count, published_at, author_name))
                    
                    comment_count += 1
                
                print(f"  💬 댓글 {comment_count}개 수집")
            
            # 변경사항 저장
            conn.commit()
            print(f"✅ {title}: 완료")
            
        except Exception as e:
            print(f"❌ {title}: 오류 발생 - {str(e)}")
            continue
    
    conn.close()
    print("\n🎉 YouTube 데이터 수집 완료!")

if __name__ == "__main__":
    collect_video_thumbnails_and_comments()
