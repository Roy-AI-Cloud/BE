"""
ROI 분석 서비스
"""
from typing import Dict, List
from app.ml import calculate_sentiment_score
from app.schemas.roi import SentimentScore, ROIEstimate, TotalScore, WeightConfig

class ROIService:
    """ROI 분석 관련 서비스"""
    
    def analyze_sentiment(self, channel_id: str, comments: List[str]) -> SentimentScore:
        """감성 분석 수행 - 극단적 점수 분포"""
        sentiment_data = calculate_sentiment_score(comments)
        
        # 기본 점수에서 극단적 조정
        base_score = sentiment_data["score"]
        
        # 긍정 비율이 높으면 보너스, 부정 비율이 높으면 페널티
        positive_bonus = sentiment_data["positive_ratio"] * 30
        negative_penalty = sentiment_data["negative_ratio"] * 40
        
        # 댓글 수가 많으면 신뢰도 보너스
        comment_bonus = min(10, len(comments) / 10)
        
        adjusted_score = max(0, min(100, base_score + positive_bonus - negative_penalty + comment_bonus))
        
        return SentimentScore(
            score=round(adjusted_score, 2),
            positive_ratio=sentiment_data["positive_ratio"],
            negative_ratio=sentiment_data["negative_ratio"],
            neutral_ratio=sentiment_data["neutral_ratio"],
            total_comments=sentiment_data["total_comments"]
        )
    
    def estimate_roi(
        self,
        channel_id: str,
        subscriber_count: int,
        avg_views: int,
        engagement_rate: float
    ) -> ROIEstimate:
        """ROI 추정 계산"""
        
        # 예상 조회수 (구독자 수 기반으로 현실적 계산)
        # 일반적으로 조회수는 구독자 수의 10-30% 정도
        if subscriber_count > 1000000:
            estimated_views = int(subscriber_count * 0.15)  # 15%
        elif subscriber_count > 100000:
            estimated_views = int(subscriber_count * 0.20)  # 20%
        elif subscriber_count > 10000:
            estimated_views = int(subscriber_count * 0.25)  # 25%
        else:
            estimated_views = int(subscriber_count * 0.30)  # 30%
        
        # 예상 참여율 (기존 참여율 기반)
        estimated_engagement = min(engagement_rate * 1.1, 10.0)  # 10% 증가, 최대 10%
        
        # 인플루언서 협찬비 계산 (구독자 수 기반)
        if subscriber_count < 10000:
            cost_per_10k_subs = 5   # 1만명당 5만원
        elif subscriber_count < 100000:
            cost_per_10k_subs = 8   # 1만명당 8만원
        elif subscriber_count < 1000000:
            cost_per_10k_subs = 12  # 1만명당 12만원
        else:
            cost_per_10k_subs = 20  # 1만명당 20만원
        
        # 예상 협찬비 계산 (만원 단위)
        estimated_cost_value = (subscriber_count / 10000) * cost_per_10k_subs * 10000  # 원 단위
        estimated_cost = self._format_cost(estimated_cost_value)
        
        # ROI 점수 계산 (0-100) - 실제 데이터 범위 반영
        view_to_subscriber_ratio = estimated_views / max(subscriber_count, 1)
        
        # 참여율 점수 (0-60점) - 실제 데이터: 1.09% ~ 5373.99%
        if engagement_rate > 1000:
            engagement_score = 60
        elif engagement_rate > 500:
            engagement_score = 55
        elif engagement_rate > 200:
            engagement_score = 50
        elif engagement_rate > 100:
            engagement_score = 45
        elif engagement_rate > 50:
            engagement_score = 40
        elif engagement_rate > 20:
            engagement_score = 30
        elif engagement_rate > 10:
            engagement_score = 20
        elif engagement_rate > 5:
            engagement_score = 10
        else:
            engagement_score = 0
        
        # 조회수/구독자 비율 점수 (0-25점)
        if view_to_subscriber_ratio > 1.0:
            view_ratio_score = 25
        elif view_to_subscriber_ratio > 0.5:
            view_ratio_score = 20
        elif view_to_subscriber_ratio > 0.2:
            view_ratio_score = 15
        elif view_to_subscriber_ratio > 0.1:
            view_ratio_score = 10
        else:
            view_ratio_score = 0
        
        # 구독자 수 점수 (0-15점)
        if subscriber_count >= 1000000:
            subscriber_score = 15
        elif subscriber_count >= 100000:
            subscriber_score = 10
        elif subscriber_count >= 10000:
            subscriber_score = 5
        else:
            subscriber_score = 0
        
        roi_score = engagement_score + view_ratio_score + subscriber_score
        
        return ROIEstimate(
            score=round(roi_score, 2),
            estimated_views=estimated_views,
            estimated_engagement=round(estimated_engagement, 2),
            estimated_cost=estimated_cost,
            cpm=cost_per_10k_subs  # 1만명당 협찬비(만원)
        )
    
    def calculate_total_score(
        self,
        brand_score: float,
        sentiment_score: float,
        roi_score: float,
        weights: WeightConfig
    ) -> TotalScore:
        """종합 점수 계산 (정규화 적용)"""
        
        # 각 점수를 0-100 범위로 정규화
        normalized_brand = self._normalize_score(brand_score, 0, 100)
        normalized_sentiment = self._normalize_score(sentiment_score, 0, 100) 
        normalized_roi = self._normalize_score(roi_score, 0, 100)
        
        # 가중 평균 계산
        total_score = (
            normalized_brand * weights.brand_image_weight +
            normalized_sentiment * weights.sentiment_weight +
            normalized_roi * weights.roi_weight
        )
        
        # 시그모이드 함수로 점수 분포 조정 (더 고른 분포)
        adjusted_score = self._sigmoid_adjustment(total_score)
        
        # 등급 계산
        grade = self._calculate_grade(adjusted_score)
        
        # 추천 메시지 생성
        recommendation = self._generate_recommendation(adjusted_score, grade)
        
        return TotalScore(
            total_score=round(adjusted_score, 2),
            grade=grade,
            recommendation=recommendation,
            weights_used=weights
        )
    
    def _normalize_score(self, score: float, min_val: float, max_val: float) -> float:
        """점수를 0-100 범위로 정규화"""
        if max_val == min_val:
            return 50.0
        normalized = ((score - min_val) / (max_val - min_val)) * 100
        return max(0, min(100, normalized))
    
    def _sigmoid_adjustment(self, score: float) -> float:
        """점수 분포를 S~D 등급에 고르게 분산"""
        import math
        
        # 입력 점수를 기반으로 더 넓은 범위의 출력 생성
        # 30-95 범위로 확장하여 모든 등급이 나올 수 있도록 조정
        
        # 1단계: 점수를 0-1 범위로 정규화
        normalized = score / 100
        
        # 2단계: 지수 함수로 분포 조정 (상위 점수에 더 많은 가중치)
        adjusted = math.pow(normalized, 0.7)  # 0.7 지수로 곡선 조정
        
        # 3단계: 30-95 범위로 확장
        final_score = 30 + (adjusted * 65)
        
        return max(30, min(95, final_score))
    
    def _format_cost(self, cost: float) -> str:
        """비용을 읽기 쉬운 형태로 포맷"""
        if cost < 10000:
            return f"{int(cost):,}원"
        elif cost < 100000000:
            return f"{int(cost/10000)}만원"
        else:
            return f"{int(cost/100000000)}억원"
    
    def _calculate_grade(self, score: float) -> str:
        """점수를 등급으로 변환"""
        if score >= 90:
            return "S"
        elif score >= 80:
            return "A"
        elif score >= 70:
            return "B"
        elif score >= 60:
            return "C"
        else:
            return "D"
    
    def _generate_recommendation(self, score: float, grade: str) -> str:
        """등급 기반 추천 메시지"""
        recommendations = {
            "S": "매우 우수한 마케팅 파트너입니다. 즉시 협업을 추천합니다.",
            "A": "우수한 마케팅 효과가 예상됩니다. 협업을 적극 추천합니다.",
            "B": "양호한 마케팅 효과가 예상됩니다. 협업을 고려해볼 만합니다.",
            "C": "보통 수준의 마케팅 효과가 예상됩니다. 신중한 검토가 필요합니다.",
            "D": "마케팅 효과가 제한적일 수 있습니다. 다른 옵션을 고려해보세요."
        }
        return recommendations.get(grade, "분석 결과를 검토해주세요.")

# 서비스 인스턴스
roi_service = ROIService()
