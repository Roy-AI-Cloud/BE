"""
텍스트 임베딩 및 유사도 계산
"""
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from typing import List
from .model_manager import model_manager

def calculate_text_similarity(text1: str, text2: str) -> float:
    """두 텍스트 간의 유사도 계산"""
    try:
        sbert_model = model_manager.get_sbert_model()
        
        # 임베딩 생성
        embeddings = sbert_model.encode([text1, text2])
        
        # 코사인 유사도 계산
        similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
        
        # 0-100 스케일로 변환
        return max(0, min(100, (similarity + 1) * 50))
        
    except Exception as e:
        print(f"[Error] 텍스트 유사도 계산 실패: {e}")
        return 50.0

def calculate_brand_channel_compatibility(
    brand_description: str,
    brand_tone: str,
    brand_category: str,
    channel_description: str,
    channel_titles: List[str]
) -> float:
    """브랜드와 채널 간의 텍스트 기반 적합도 계산"""
    try:
        sbert_model = model_manager.get_sbert_model()
        
        # 브랜드 정보 결합
        brand_text = f"{brand_description} {brand_tone} {brand_category}"
        
        # 채널 정보 결합
        channel_text = f"{channel_description} " + " ".join(channel_titles[:10])
        
        # 임베딩 생성
        embeddings = sbert_model.encode([brand_text, channel_text])
        
        # 유사도 계산
        similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
        
        # 0-100 스케일로 변환
        return max(0, min(100, (similarity + 1) * 50))
        
    except Exception as e:
        print(f"[Error] 브랜드-채널 적합도 계산 실패: {e}")
        return 50.0

def extract_keywords(texts: List[str], top_k: int = 10) -> List[str]:
    """텍스트에서 키워드 추출 (간단한 빈도 기반)"""
    try:
        import re
        from collections import Counter
        
        # 텍스트 전처리 및 단어 추출
        all_words = []
        for text in texts:
            # 한글, 영문, 숫자만 추출
            words = re.findall(r'[가-힣a-zA-Z0-9]+', text)
            # 2글자 이상 단어만 포함
            words = [word for word in words if len(word) >= 2]
            all_words.extend(words)
        
        # 빈도 계산 및 상위 키워드 반환
        word_counts = Counter(all_words)
        return [word for word, count in word_counts.most_common(top_k)]
        
    except Exception as e:
        print(f"[Error] 키워드 추출 실패: {e}")
        return []
