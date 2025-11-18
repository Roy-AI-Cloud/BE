"""
기존 비디오 데이터에 샘플 썸네일 URL 추가
"""
import sqlite3
import random

def add_sample_thumbnails():
    """기존 비디오에 샘플 썸네일 URL 추가"""
    
    # 샘플 썸네일 URL들 (실제 YouTube 썸네일 형식)
    sample_thumbnails = [
        "https://i.ytimg.com/vi/dQw4w9WgXcQ/mqdefault.jpg",
        "https://i.ytimg.com/vi/9bZkp7q19f0/mqdefault.jpg", 
        "https://i.ytimg.com/vi/kJQP7kiw5Fk/mqdefault.jpg",
        "https://i.ytimg.com/vi/L_jWHffIx5E/mqdefault.jpg",
        "https://i.ytimg.com/vi/ZZ5LpwO-An4/mqdefault.jpg",
        "https://i.ytimg.com/vi/fJ9rUzIMcZQ/mqdefault.jpg",
        "https://i.ytimg.com/vi/Ct6BUPvE2sM/mqdefault.jpg",
        "https://i.ytimg.com/vi/oHg5SJYRHA0/mqdefault.jpg",
        "https://i.ytimg.com/vi/hFZFjoX2cGg/mqdefault.jpg",
        "https://i.ytimg.com/vi/y6120QOlsfU/mqdefault.jpg"
    ]
    
    conn = sqlite3.connect('db/influencer.db')
    cursor = conn.cursor()
    
    # 썸네일이 없는 비디오들 조회
    cursor.execute("SELECT video_id, video_title FROM video WHERE thumbnail_url IS NULL OR thumbnail_url = ''")
    videos = cursor.fetchall()
    
    print(f"📸 {len(videos)}개 비디오에 썸네일 URL 추가 중...")
    
    for video_id, video_title in videos:
        # 랜덤 썸네일 URL 선택
        thumbnail_url = random.choice(sample_thumbnails)
        
        # 업데이트
        cursor.execute("""
            UPDATE video 
            SET thumbnail_url = ? 
            WHERE video_id = ?
        """, (thumbnail_url, video_id))
        
        print(f"  ✅ {video_title[:30]}... → 썸네일 추가")
    
    conn.commit()
    conn.close()
    
    print(f"🎉 {len(videos)}개 비디오 썸네일 URL 추가 완료!")

if __name__ == "__main__":
    add_sample_thumbnails()
