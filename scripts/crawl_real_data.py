#!/usr/bin/env python3
import os
import sys
import time
from datetime import datetime
from googleapiclient.discovery import build
from sqlalchemy import text

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.core.models import Influencer, Video, Comment
from app.core.database import get_session

# 환경변수에서 API 키 로드
from dotenv import load_dotenv
load_dotenv()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
if not YOUTUBE_API_KEY:
    print("❌ YOUTUBE_API_KEY가 설정되지 않았습니다.")
    sys.exit(1)

youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

def get_video_comments(video_id, target_count=150):
    """비디오의 댓글 100-200개 가져오기"""
    try:
        comments = []
        next_page_token = None
        
        while len(comments) < target_count:
            response = youtube.commentThreads().list(
                part='snippet',
                videoId=video_id,
                maxResults=min(100, target_count - len(comments)),
                order='relevance',
                pageToken=next_page_token
            ).execute()
            
            for item in response['items']:
                comment = item['snippet']['topLevelComment']['snippet']
                comments.append({
                    'comment_text': comment['textDisplay'][:300],
                    'like_count': comment['likeCount'],
                    'published_at': comment['publishedAt']
                })
            
            next_page_token = response.get('nextPageToken')
            if not next_page_token:
                break
                
        return comments[:target_count]
        
    except Exception as e:
        print(f"비디오 {video_id} 댓글 가져오기 실패: {e}")
        return []

def get_channel_videos(channel_id, max_results=5):
    """채널의 최신 비디오 목록 가져오기"""
    try:
        channels_response = youtube.channels().list(
            part='contentDetails',
            id=channel_id
        ).execute()
        
        if not channels_response['items']:
            return []
            
        uploads_playlist_id = channels_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
        
        playlist_response = youtube.playlistItems().list(
            part='snippet',
            playlistId=uploads_playlist_id,
            maxResults=max_results
        ).execute()
        
        video_ids = [item['snippet']['resourceId']['videoId'] for item in playlist_response['items']]
        
        videos_response = youtube.videos().list(
            part='snippet,statistics',
            id=','.join(video_ids)
        ).execute()
        
        videos = []
        for video in videos_response['items']:
            videos.append({
                'video_id': video['id'],
                'title': video['snippet']['title'],
                'description': video['snippet']['description'][:500],
                'published_at': video['snippet']['publishedAt'],
                'thumbnail_url': video['snippet']['thumbnails']['high']['url'],
                'view_count': int(video['statistics'].get('viewCount', 0)),
                'like_count': int(video['statistics'].get('likeCount', 0)),
                'comment_count': int(video['statistics'].get('commentCount', 0))
            })
        
        return videos
        
    except Exception as e:
        print(f"채널 {channel_id} 비디오 가져오기 실패: {e}")
        return []

def crawl_influencer_data(session, channel_id, channel_name):
    """특정 인플루언서의 실제 데이터 크롤링"""
    print(f"\n=== {channel_name} ({channel_id}) 크롤링 시작 ===")
    
    # 기존 데이터 삭제
    session.execute(text("DELETE FROM comment WHERE channel_id = :channel_id"), {"channel_id": channel_id})
    session.execute(text("DELETE FROM video WHERE channel_id = :channel_id"), {"channel_id": channel_id})
    session.commit()
    
    # 비디오 데이터 가져오기
    videos = get_channel_videos(channel_id, max_results=5)
    
    if not videos:
        print(f"❌ {channel_name}: 비디오 데이터 없음")
        return
    
    print(f"✅ {len(videos)}개 비디오 발견")
    
    for video_data in videos:
        # 비디오 저장
        video = Video(
            video_id=video_data['video_id'],
            channel_id=channel_id,
            video_title=video_data['title'],
            video_published_at=datetime.fromisoformat(video_data['published_at'].replace('Z', '+00:00')),
            thumbnail_url=video_data['thumbnail_url'],
            view_count=video_data['view_count'],
            like_count=video_data['like_count'],
            comment_count=video_data['comment_count']
        )
        session.add(video)
        
        # 댓글 100-200개 가져오기
        comments = get_video_comments(video_data['video_id'], target_count=150)
        
        for comment_data in comments:
            comment = Comment(
                video_id=video_data['video_id'],
                channel_id=channel_id,
                comment_text=comment_data['comment_text'],
                like_count=comment_data['like_count'],
                published_at=datetime.fromisoformat(comment_data['published_at'].replace('Z', '+00:00'))
            )
            session.add(comment)
        
        print(f"  📹 {video_data['title'][:50]}... ({len(comments)}개 댓글)")
        time.sleep(2)  # API 할당량 보호
    
    session.commit()
    print(f"✅ {channel_name} 크롤링 완료")

def main():
    if not YOUTUBE_API_KEY:
        print("❌ YOUTUBE_API_KEY가 설정되지 않았습니다.")
        return
    
    session = next(get_session())
    
    try:
        influencers = session.query(Influencer).all()
        print(f"📊 총 {len(influencers)}명의 인플루언서 발견")
        
        for i, influencer in enumerate(influencers, 1):
            print(f"\n[{i}/{len(influencers)}]", end=" ")
            crawl_influencer_data(session, influencer.channel_id, influencer.title or "Unknown")
            
            if i < len(influencers):
                print("⏳ 5초 대기...")
                time.sleep(5)
        
        print(f"\n🎉 모든 인플루언서 데이터 크롤링 완료!")
        
    except Exception as e:
        print(f"❌ 크롤링 중 오류 발생: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    main()
