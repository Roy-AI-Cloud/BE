from sqlmodel import Session, select
from app.core.database import engine
from app.core.models import Influencer, Video
from datetime import datetime, timedelta
import random

def create_sample_videos():
    """샘플 비디오 데이터 생성"""
    
    with Session(engine) as session:
        # 모든 인플루언서 가져오기
        influencers = session.exec(select(Influencer)).all()
        
        print(f"📹 {len(influencers)}명의 인플루언서에 대해 샘플 비디오 생성 중...")
        
        for inf in influencers:  # 전체 49명
            # 기존 비디오가 있는지 확인
            existing = session.exec(
                select(Video).where(Video.channel_id == inf.channel_id)
            ).first()
            
            if existing:
                print(f"⏭️  {inf.title}: 이미 비디오 존재")
                continue
            
            # 각 인플루언서당 3-5개 비디오 생성
            video_count = random.randint(3, 5)
            
            for i in range(video_count):
                # 샘플 비디오 데이터
                video = Video(
                    video_id=f"sample_{inf.channel_id}_{i}",
                    video_title=f"{inf.title} - 샘플 영상 {i+1}",
                    video_published_at=datetime.now() - timedelta(days=random.randint(1, 30)),
                    view_count=random.randint(1000, 100000),
                    like_count=random.randint(50, 5000),
                    comment_count=random.randint(10, 500),
                    channel_id=inf.channel_id
                )
                session.add(video)
            
            print(f"✅ {inf.title}: {video_count}개 비디오 생성")
        
        session.commit()
        print(f"\n🎉 전체 인플루언서 비디오 데이터 생성 완료!")

if __name__ == "__main__":
    create_sample_videos()
