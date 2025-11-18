"""
감성 분석 모듈 - KoBERT 기반 + 사전 기반 fallback
"""
import torch
from typing import List, Dict, Tuple
from collections import Counter
import re
from .model_manager import model_manager

# 감성 사전 (fallback용)
POSITIVE_WORDS = [
    "좋다", "최고", "대박", "완전", "진짜", "정말", "너무", "예쁘다", "멋지다", "훌륭하다",
    "감사", "고마워", "사랑", "행복", "기쁘다", "웃음", "재미", "유용", "도움", "추천"
]

NEGATIVE_WORDS = [
    "싫다", "별로", "안좋다", "나쁘다", "최악", "짜증", "화나다", "실망", "후회", "문제",
    "어렵다", "힘들다", "복잡", "불편", "아쉽다", "부족", "비싸다", "느리다", "답답"
]

def analyze_sentiment_kobert(texts: List[str]) -> List[Dict]:
    """KoBERT를 사용한 감성분석"""
    try:
        model, tokenizer = model_manager.get_kobert_model()
        if model is None or tokenizer is None:
            return analyze_sentiment_dictionary(texts)
        
        device = model_manager.device
        results = []
        
        for text in texts:
            # 토큰화
            inputs = tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                padding=True,
                max_length=512
            ).to(device)
            
            # 예측
            with torch.no_grad():
                outputs = model(**inputs)
                predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
                predicted_class = torch.argmax(predictions, dim=-1).item()
                confidence = predictions[0][predicted_class].item()
            
            # 결과 매핑 (0: negative, 1: neutral, 2: positive)
            sentiment_map = {0: "negative", 1: "neutral", 2: "positive"}
            
            results.append({
                "text": text,
                "sentiment": sentiment_map[predicted_class],
                "confidence": confidence,
                "scores": {
                    "negative": predictions[0][0].item(),
                    "neutral": predictions[0][1].item(),
                    "positive": predictions[0][2].item()
                }
            })
        
        return results
        
    except Exception as e:
        print(f"[Error] KoBERT 감성분석 실패: {e}")
        return analyze_sentiment_dictionary(texts)

def analyze_sentiment_dictionary(texts: List[str]) -> List[Dict]:
    """사전 기반 감성분석 (fallback)"""
    results = []
    
    for text in texts:
        text_clean = re.sub(r'[^\w\s]', '', text.lower())
        
        positive_count = sum(1 for word in POSITIVE_WORDS if word in text_clean)
        negative_count = sum(1 for word in NEGATIVE_WORDS if word in text_clean)
        
        if positive_count > negative_count:
            sentiment = "positive"
            confidence = min(0.8, 0.5 + (positive_count - negative_count) * 0.1)
        elif negative_count > positive_count:
            sentiment = "negative"
            confidence = min(0.8, 0.5 + (negative_count - positive_count) * 0.1)
        else:
            sentiment = "neutral"
            confidence = 0.5
        
        results.append({
            "text": text,
            "sentiment": sentiment,
            "confidence": confidence,
            "scores": {
                "positive": positive_count / max(1, positive_count + negative_count),
                "negative": negative_count / max(1, positive_count + negative_count),
                "neutral": 0.5 if positive_count == negative_count else 0.2
            }
        })
    
    return results

def calculate_sentiment_score(comments: List[str]) -> Dict:
    """댓글 리스트의 종합 감성 점수 계산"""
    if not comments:
        return {
            "score": 50.0,
            "positive_ratio": 0.33,
            "negative_ratio": 0.33,
            "neutral_ratio": 0.34,
            "total_comments": 0
        }
    
    # 감성분석 실행
    results = analyze_sentiment_kobert(comments)
    
    # 통계 계산
    sentiment_counts = Counter(result["sentiment"] for result in results)
    total = len(results)
    
    positive_ratio = sentiment_counts.get("positive", 0) / total
    negative_ratio = sentiment_counts.get("negative", 0) / total
    neutral_ratio = sentiment_counts.get("neutral", 0) / total
    
    # 점수 계산 (긍정 비율 기반, 0-100)
    score = (positive_ratio * 100 + neutral_ratio * 50) * 0.8 + 20
    
    return {
        "score": min(100, max(0, score)),
        "positive_ratio": positive_ratio,
        "negative_ratio": negative_ratio,
        "neutral_ratio": neutral_ratio,
        "total_comments": total
    }
