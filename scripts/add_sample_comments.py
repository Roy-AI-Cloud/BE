"""
비디오별 현실적인 샘플 댓글 생성
"""
import sqlite3
import random
from datetime import datetime, timedelta

def generate_sample_comments():
    """각 비디오에 현실적인 샘플 댓글 추가"""
    
    # 카테고리별 댓글 템플릿
    comment_templates = {
        "뷰티": [
            "정말 유용한 팁이네요! 감사합니다 ❤️",
            "이 제품 써봤는데 정말 좋더라구요",
            "언니 피부가 너무 예뻐요 ㅠㅠ",
            "튜토리얼 따라해봤는데 잘 안되네요 ㅋㅋ",
            "다음에는 어떤 브랜드 리뷰 해주실건가요?",
            "구독했어요! 항상 좋은 영상 감사해요",
            "이 색깔 진짜 예쁘다",
            "가격대가 어떻게 되나요?",
            "민감성 피부도 괜찮을까요?",
            "어디서 살 수 있나요?"
        ],
        "패션": [
            "스타일링 너무 예뻐요!",
            "어디 브랜드 제품인가요?",
            "가격이 궁금해요",
            "키 몇이신가요? 참고하려구요",
            "코디 따라해봐야겠어요",
            "옷 정보 좀 알려주세요!",
            "이런 스타일 좋아해요 ㅎㅎ",
            "어울리는 신발도 추천해주세요",
            "겨울 코디도 보고싶어요",
            "쇼핑몰 정보 공유해주세요"
        ],
        "일상": [
            "일상이 너무 힐링돼요",
            "브이로그 보는 재미가 있어요",
            "저도 이런 일상 살고싶다",
            "편집 스킬이 좋으시네요",
            "음식 맛있어보여요!",
            "어디 가신건가요?",
            "일상 공유해주셔서 감사해요",
            "힐링되는 영상이네요",
            "카메라 뭐 쓰시나요?",
            "다음 브이로그도 기대할게요"
        ],
        "요리": [
            "레시피 감사해요!",
            "따라 만들어봤는데 맛있어요",
            "재료 어디서 사셨나요?",
            "초보도 할 수 있을까요?",
            "간단해서 좋네요",
            "가족들이 좋아할 것 같아요",
            "다음에는 디저트 레시피도 해주세요",
            "칼로리는 어느정도 될까요?",
            "보기만 해도 배고파져요 ㅠㅠ",
            "요리 초보인데 도움 많이 됐어요"
        ]
    }
    
    # 부정적 댓글 (소수)
    negative_comments = [
        "별로네요",
        "기대했는데 아쉬워요",
        "다른 영상이 더 좋았어요",
        "너무 길어요",
        "음질이 안좋네요"
    ]
    
    conn = sqlite3.connect('db/influencer.db')
    cursor = conn.cursor()
    
    # 모든 비디오와 채널 정보 조회
    cursor.execute("""
        SELECT v.video_id, v.video_title, v.channel_id, i.category, i.title as channel_title
        FROM video v
        JOIN influencer i ON v.channel_id = i.channel_id
    """)
    videos = cursor.fetchall()
    
    print(f"💬 {len(videos)}개 비디오에 댓글 생성 중...")
    
    total_comments = 0
    
    for video_id, video_title, channel_id, category, channel_title in videos:
        # 카테고리에 맞는 댓글 템플릿 선택
        if category and category in comment_templates:
            templates = comment_templates[category]
        else:
            templates = comment_templates["일상"]  # 기본값
        
        # 비디오당 5-15개 댓글 생성
        comment_count = random.randint(5, 15)
        
        for i in range(comment_count):
            # 90% 긍정, 10% 부정
            if random.random() < 0.9:
                comment_text = random.choice(templates)
            else:
                comment_text = random.choice(negative_comments)
            
            # 댓글 ID 생성
            comment_id = f"comment_{video_id}_{i+1}"
            
            # 좋아요 수 (0-50)
            like_count = random.randint(0, 50)
            
            # 발행일 (최근 30일 내)
            days_ago = random.randint(1, 30)
            published_at = (datetime.now() - timedelta(days=days_ago)).isoformat()
            
            # 작성자 이름
            author_names = ["김민수", "이영희", "박철수", "최지영", "정민호", "한소영", "윤태현", "임수진"]
            author_name = random.choice(author_names)
            
            # 댓글 저장
            cursor.execute("""
                INSERT OR IGNORE INTO comment 
                (comment_id, video_id, channel_id, comment_text, like_count, published_at, author_name)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (comment_id, video_id, channel_id, comment_text, like_count, published_at, author_name))
            
            total_comments += 1
        
        print(f"  ✅ {channel_title} - {video_title[:20]}... ({comment_count}개 댓글)")
    
    conn.commit()
    conn.close()
    
    print(f"🎉 총 {total_comments}개 댓글 생성 완료!")

if __name__ == "__main__":
    generate_sample_comments()
