"""
ROI 분석 서비스
"""
from typing import Dict, List
from app.ml import calculate_sentiment_score
from app.schemas.roi import SentimentScore, ROIEstimate, TotalScore, WeightConfig

class ROIService:
    """ROI 분석 관련 서비스"""
    
    def analyze_sentiment(self, channel_id: str, comments: List[str]) -> SentimentScore:
        """감성 분석 수행"""
        sentiment_data = calculate_sentiment_score(comments)
        
        return SentimentScore(
            score=sentiment_data["score"],
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
        
        # 예상 조회수 (최근 평균 기반)
        estimated_views = int(avg_views * 1.2)  # 20% 증가 가정
        
        # 예상 참여율 (기존 참여율 기반)
        estimated_engagement = min(engagement_rate * 1.1, 10.0)  # 10% 증가, 최대 10%
        
        # CPM 계산 (구독자 수 기반)
        if subscriber_count < 10000:
            cpm = 500
        elif subscriber_count < 100000:
            cpm = 800
        elif subscriber_count < 1000000:
            cpm = 1200
        else:
            cpm = 2000
        
        # 예상 비용 계산
        estimated_cost_value = (estimated_views / 1000) * cpm
        estimated_cost = self._format_cost(estimated_cost_value)
        
        # ROI 점수 계산 (0-100)
        # 참여율, 조회수 대비 구독자 비율 등을 고려
        view_to_subscriber_ratio = estimated_views / max(subscriber_count, 1)
        roi_score = min(100, (estimated_engagement * 5) + (view_to_subscriber_ratio * 30) + 20)
        
        return ROIEstimate(
            score=round(roi_score, 2),
            estimated_views=estimated_views,
            estimated_engagement=round(estimated_engagement, 2),
            estimated_cost=estimated_cost,
            cpm=cpm
        )
    
    def calculate_total_score(
        self,
        brand_score: float,
        sentiment_score: float,
        roi_score: float,
        weights: WeightConfig
    ) -> TotalScore:
        """종합 점수 계산"""
        
        # 가중 평균 계산
        total_score = (
            brand_score * weights.brand_image_weight +
            sentiment_score * weights.sentiment_weight +
            roi_score * weights.roi_weight
        )
        
        # 등급 계산
        grade = self._calculate_grade(total_score)
        
        # 추천 메시지 생성
        recommendation = self._generate_recommendation(total_score, grade)
        
        return TotalScore(
            total_score=round(total_score, 2),
            grade=grade,
            recommendation=recommendation,
            weights_used=weights
        )
    
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
