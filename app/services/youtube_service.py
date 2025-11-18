"""
YouTube 관련 비즈니스 로직
"""
import os
import time
import httpx
from typing import List, Dict, Optional
from fastapi import HTTPException
from sqlmodel import Session, select, func
from app.core import Influencer, get_session
from app.schemas.youtube import ChannelDetails, HomeYoutuberCard, ChannelWithMetrics
from app.config import settings

# YouTube API 설정
API_KEY = os.getenv("YOUTUBE_API_KEY", "")
if not API_KEY:
    print("Warning: YOUTUBE_API_KEY not found in environment variables")

YOUTUBE_BASE_URL = "https://www.googleapis.com/youtube/v3"

class YouTubeService:
    """YouTube 관련 서비스"""
    
    def __init__(self):
        self.api_key = API_KEY
    
    def _make_request(self, endpoint: str, params: dict) -> dict:
        """YouTube API 요청"""
        url = f"{YOUTUBE_BASE_URL}/{endpoint}"
        params["key"] = self.api_key
        
        with httpx.Client(timeout=20) as client:
            response = client.get(url, params=params)
            if response.status_code >= 400:
                raise HTTPException(status_code=response.status_code, detail=response.text)
            return response.json()
    
    def get_home_youtubers(self, session: Session, limit: int = 50) -> List[HomeYoutuberCard]:
        """홈 화면용 유튜버 리스트 조회"""
        statement = select(Influencer).order_by(func.random()).limit(limit)
        influencers = session.exec(statement).all()
        
        return [
            HomeYoutuberCard(
                channel_id=inf.channel_id,
                title=inf.title or "Unknown",
                subscriber_count=inf.subscriber_count,
                thumbnail_url=inf.thumbnail_url,
                category=inf.category or "미분류",
                engagement_rate=inf.engagement_rate,
                estimated_price=inf.estimated_price or "가격 문의"
            )
            for inf in influencers
        ]
    
    def search_channels(self, keyword: str, max_results: int = 30) -> List[ChannelWithMetrics]:
        """키워드로 채널 검색"""
        try:
            params = {
                "part": "snippet",
                "type": "channel",
                "q": keyword,
                "maxResults": min(max_results, 50),
                "regionCode": "KR",
                "relevanceLanguage": "ko"
            }
            
            data = self._make_request("search", params)
            channel_ids = [item["id"]["channelId"] for item in data.get("items", [])]
            
            if not channel_ids:
                return []
            
            return self._get_channel_details(channel_ids)
            
        except Exception as e:
            print(f"[Error] 채널 검색 실패: {e}")
            return []
    
    def get_popular_channels_from_db(self, session: Session, max_results: int = 50) -> List[ChannelWithMetrics]:
        """DB에서 인기 채널 조회 (구독자 수 기준)"""
        from app.core.models import Influencer
        from sqlmodel import select, desc
        
        try:
            # 구독자 수 기준으로 정렬하여 조회
            statement = select(Influencer).order_by(desc(Influencer.subscriber_count)).limit(max_results)
            influencers = session.exec(statement).all()
            
            return [
                ChannelWithMetrics(
                    channel_id=inf.channel_id,
                    title=inf.title or "Unknown",
                    subscriber_count=inf.subscriber_count,
                    view_count=inf.view_count,
                    video_count=inf.video_count,
                    thumbnail_url=inf.thumbnail_url,
                    engagement_rate=inf.engagement_rate,
                    estimated_price=inf.estimated_price or f"{inf.subscriber_count // 1000}만원" if inf.subscriber_count else "가격 문의",
                    category=inf.category or "미분류"
                )
                for inf in influencers
            ]
            
        except Exception as e:
            print(f"[Error] DB 인기 채널 조회 실패: {e}")
            return []

    def get_popular_channels(self, max_results: int = 50) -> List[ChannelWithMetrics]:
        """인기 채널 조회"""
        try:
            # 인기 동영상을 통해 채널 찾기
            params = {
                "part": "snippet",
                "chart": "mostPopular",
                "regionCode": "KR",
                "maxResults": max_results,
                "videoCategoryId": "22"  # People & Blogs
            }
            
            data = self._make_request("videos", params)
            channel_ids = list(set(item["snippet"]["channelId"] for item in data.get("items", [])))
            
            return self._get_channel_details(channel_ids[:max_results])
            
        except Exception as e:
            print(f"[Error] 인기 채널 조회 실패: {e}")
            return []
    
    def _get_channel_details(self, channel_ids: List[str]) -> List[ChannelWithMetrics]:
        """채널 상세 정보 조회"""
        if not channel_ids:
            return []
        
        try:
            params = {
                "part": "snippet,statistics,brandingSettings",
                "id": ",".join(channel_ids[:50])  # API 제한
            }
            
            data = self._make_request("channels", params)
            results = []
            
            for item in data.get("items", []):
                snippet = item.get("snippet", {})
                stats = item.get("statistics", {})
                thumbnails = snippet.get("thumbnails", {})
                
                # 썸네일 URL 추출
                thumbnail_url = None
                for size in ["high", "medium", "default"]:
                    if size in thumbnails:
                        thumbnail_url = thumbnails[size]["url"]
                        break
                
                # 참여율 계산 (간단한 추정)
                subscriber_count = int(stats.get("subscriberCount", 0))
                view_count = int(stats.get("viewCount", 0))
                video_count = int(stats.get("videoCount", 1))
                
                avg_views = view_count / max(video_count, 1)
                engagement_rate = min(10.0, (avg_views / max(subscriber_count, 1)) * 100) if subscriber_count > 0 else 0
                
                results.append(ChannelWithMetrics(
                    channel_id=item["id"],
                    title=snippet.get("title", "Unknown"),
                    subscriber_count=subscriber_count,
                    view_count=view_count,
                    video_count=video_count,
                    thumbnail_url=thumbnail_url,
                    engagement_rate=round(engagement_rate, 2),
                    estimated_price=self._estimate_price(subscriber_count),
                    category="미분류"
                ))
            
            return results
            
        except Exception as e:
            print(f"[Error] 채널 상세 정보 조회 실패: {e}")
            return []
    
    def _estimate_price(self, subscriber_count: int) -> str:
        """구독자 수 기반 예상 가격 계산"""
        if subscriber_count < 1000:
            return "10-50만원"
        elif subscriber_count < 10000:
            return "50-200만원"
        elif subscriber_count < 100000:
            return "200-500만원"
        elif subscriber_count < 1000000:
            return "500-2000만원"
        else:
            return "2000만원 이상"
    
    def get_sorted_youtubers(self, session: Session, sort_by: str, limit: int) -> List[HomeYoutuberCard]:
        """정렬된 유튜버 목록 조회"""
        from sqlmodel import select, desc, asc
        
        query = select(Influencer)
        
        if sort_by == "followers":
            query = query.order_by(desc(Influencer.subscriber_count))
        elif sort_by == "engagement":
            query = query.order_by(desc(Influencer.engagement_rate))
        elif sort_by == "price":
            query = query.order_by(asc(Influencer.subscriber_count))
        
        query = query.limit(limit)
        influencers = session.exec(query).all()
        
        return [
            HomeYoutuberCard(
                channel_id=inf.channel_id,
                title=inf.title,
                subscriber_count=inf.subscriber_count or 0,
                thumbnail_url=inf.thumbnail_url or "",
                category=inf.category or "기타",
                engagement_rate=inf.engagement_rate or 0.0,
                estimated_price=inf.estimated_price or self._estimate_price(inf.subscriber_count or 0)
            )
            for inf in influencers
        ]

# 서비스 인스턴스
youtube_service = YouTubeService()
