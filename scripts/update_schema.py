"""
DB 스키마 업데이트: 썸네일 및 댓글 테이블 추가
"""
import sqlite3
from datetime import datetime

def update_database_schema():
    """데이터베이스 스키마 업데이트"""
    
    conn = sqlite3.connect('db/influencer.db')
    cursor = conn.cursor()
    
    try:
        # 1. Video 테이블에 thumbnail_url 컬럼 추가
        print("📝 Video 테이블에 thumbnail_url 컬럼 추가 중...")
        cursor.execute("""
            ALTER TABLE video 
            ADD COLUMN thumbnail_url VARCHAR
        """)
        print("✅ thumbnail_url 컬럼 추가 완료")
        
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("⚠️ thumbnail_url 컬럼이 이미 존재합니다")
        else:
            print(f"❌ thumbnail_url 컬럼 추가 실패: {e}")
    
    try:
        # 2. Comments 테이블 생성
        print("📝 Comments 테이블 생성 중...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS comment (
                comment_id VARCHAR PRIMARY KEY,
                video_id VARCHAR NOT NULL,
                channel_id VARCHAR NOT NULL,
                comment_text TEXT NOT NULL,
                like_count INTEGER DEFAULT 0,
                published_at DATETIME,
                author_name VARCHAR,
                FOREIGN KEY(video_id) REFERENCES video(video_id),
                FOREIGN KEY(channel_id) REFERENCES influencer(channel_id)
            )
        """)
        print("✅ Comments 테이블 생성 완료")
        
    except sqlite3.Error as e:
        print(f"❌ Comments 테이블 생성 실패: {e}")
    
    # 변경사항 저장
    conn.commit()
    conn.close()
    
    print("🎉 데이터베이스 스키마 업데이트 완료!")

if __name__ == "__main__":
    update_database_schema()
