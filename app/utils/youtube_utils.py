import httpx
from typing import List, Dict, Optional
from app.schemas.youtube import ChannelDetails, VideoStatsOut
from app.config.settings import settings

API_KEY = settings.YOUTUBE_API_KEY
YOUTUBE_BASE_URL = "https://www.googleapis.com/youtube/v3"

def search_channels_by_keyword(keyword: str, top_n: int = 50) -> List[str]:
    """키워드로 채널 검색하여 채널 ID 리스트 반환"""
    try:
        # API 키 확인
        if not API_KEY or API_KEY == "":
            print("❌ YouTube API 키가 설정되지 않았습니다.")
            return []
            
        params = {
            "part": "snippet",
            "type": "channel",
            "q": keyword,
            "maxResults": min(top_n, 50),
            "regionCode": "KR",
            "relevanceLanguage": "ko",
            "key": API_KEY
        }
        
        with httpx.Client(timeout=30) as client:
            response = client.get(f"{YOUTUBE_BASE_URL}/search", params=params)
            
            # 상세한 에러 정보 출력
            if response.status_code == 403:
                error_data = response.json() if response.content else {}
                error_reason = error_data.get('error', {}).get('errors', [{}])[0].get('reason', 'unknown')
                print(f"❌ API 403 오류: {error_reason}")
                if 'quotaExceeded' in error_reason:
                    print("   → 일일 할당량 초과. 내일 다시 시도하세요.")
                elif 'keyInvalid' in error_reason:
                    print("   → API 키가 유효하지 않습니다.")
                elif 'accessNotConfigured' in error_reason:
                    print("   → YouTube Data API v3가 활성화되지 않았습니다.")
                return []
                
            response.raise_for_status()
            data = response.json()
            
        channel_ids = [item["id"]["channelId"] for item in data.get("items", [])]
        print(f"✅ 검색 성공: {len(channel_ids)}개 채널 발견")
        return channel_ids
        
    except httpx.HTTPStatusError as e:
        print(f"❌ HTTP 오류 {e.response.status_code}: {e}")
        return []
    except Exception as e:
        print(f"❌ 채널 검색 오류: {e}")
        return []

def fetch_channel_details(channel_ids: List[str], source_tag: str = "") -> List[ChannelDetails]:
    """채널 상세 정보 조회"""
    if not channel_ids:
        return []
    
    try:
        params = {
            "part": "snippet,statistics,brandingSettings",
            "id": ",".join(channel_ids[:50]),
            "key": API_KEY
        }
        
        with httpx.Client(timeout=20) as client:
            response = client.get(f"{YOUTUBE_BASE_URL}/channels", params=params)
            response.raise_for_status()
            data = response.json()
        
        results = []
        for item in data.get("items", []):
            snippet = item.get("snippet", {})
            stats = item.get("statistics", {})
            thumbnails = snippet.get("thumbnails", {})
            
            thumbnail_url = None
            for size in ["high", "medium", "default"]:
                if size in thumbnails:
                    thumbnail_url = thumbnails[size]["url"]
                    break
            
            results.append(ChannelDetails(
                channel_id=item["id"],
                title=snippet.get("title", "Unknown"),
                description=snippet.get("description", ""),
                subscriber_count=int(stats.get("subscriberCount", 0)),
                view_count=int(stats.get("viewCount", 0)),
                video_count=int(stats.get("videoCount", 0)),
                thumbnail_url=thumbnail_url,
                published_at=snippet.get("publishedAt"),
                country=snippet.get("country")
            ))
        
        return results
    except Exception as e:
        print(f"채널 상세 정보 조회 오류: {e}")
        return []

def get_recent_video_stats(channel_id: str, num_videos: int = 5) -> List[VideoStatsOut]:
    """최근 영상 통계 조회"""
    try:
        # 1. 채널의 최근 영상 ID 가져오기
        search_params = {
            "part": "snippet",
            "channelId": channel_id,
            "type": "video",
            "order": "date",
            "maxResults": num_videos,
            "key": API_KEY
        }
        
        with httpx.Client(timeout=20) as client:
            response = client.get(f"{YOUTUBE_BASE_URL}/search", params=search_params)
            response.raise_for_status()
            search_data = response.json()
        
        video_ids = [item["id"]["videoId"] for item in search_data.get("items", [])]
        
        if not video_ids:
            return []
        
        # 2. 영상 상세 통계 가져오기
        video_params = {
            "part": "snippet,statistics",
            "id": ",".join(video_ids),
            "key": API_KEY
        }
        
        response = client.get(f"{YOUTUBE_BASE_URL}/videos", params=video_params)
        response.raise_for_status()
        video_data = response.json()
        
        results = []
        for item in video_data.get("items", []):
            snippet = item.get("snippet", {})
            stats = item.get("statistics", {})
            
            results.append(VideoStatsOut(
                channel_id=channel_id,
                title=snippet.get("channelTitle", ""),  # channel_title -> title로 통일
                video_id=item["id"],
                video_title=snippet.get("title", ""),
                video_published_at=snippet.get("publishedAt"),
                view_count=int(stats.get("viewCount", 0)),
                like_count=int(stats.get("likeCount", 0)),
                comment_count=int(stats.get("commentCount", 0))
            ))
        
        return results
    except Exception as e:
        print(f"영상 통계 조회 오류: {e}")
        return []

def calculate_engagement_rate_from_stats(video_stats: List[Dict], subscriber_count: int) -> Optional[float]:
    """영상 통계로부터 참여율 계산 (구독자 대비)"""
    if not video_stats or subscriber_count <= 0:
        return None
    
    try:
        total_engagement = 0
        
        for video in video_stats:
            views = video.get('view_count', 0)
            likes = video.get('like_count', 0)
            comments = video.get('comment_count', 0)
            total_engagement += views + likes + comments
        
        # 참여율 = (조회수 + 좋아요 + 댓글) / 구독자 수 * 100
        engagement_rate = (total_engagement / subscriber_count) * 100
        return round(engagement_rate, 2)
    except Exception as e:
        print(f"참여율 계산 오류: {e}")
        return None
