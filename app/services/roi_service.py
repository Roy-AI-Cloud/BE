"""
ROI 분석 서비스
"""
from typing import Dict, List
from app.ml import calculate_sentiment_score
from app.schemas.roi import SentimentScore, ROIEstimate, TotalScore, WeightConfig

class ROIService:
    """ROI 분석 관련 서비스"""
    
    def analyze_sentiment(self, channel_id: str, comments: List[str]) -> SentimentScore:
        """감성 분석 수행 - 극단적 점수 차별화"""
        sentiment_data = calculate_sentiment_score(comments)
        
        # 기본 점수를 더 극단적으로 조정
        base_score = sentiment_data["score"]
        
        # 긍정 비율 극대화 (최대 50점 보너스)
        positive_bonus = sentiment_data["positive_ratio"] * 50
        
        # 부정 비율 극대화 (최대 60점 페널티)  
        negative_penalty = sentiment_data["negative_ratio"] * 60
        
        # 댓글 수 보너스 확대 (최대 20점)
        comment_bonus = min(20, len(comments) / 5)
        
        # 채널별 카테고리 보너스 (뷰티/패션/요리 등)
        category_bonus = 0
        if "뷰티" in channel_id or "beauty" in channel_id.lower():
            category_bonus = 15
        elif "패션" in channel_id or "fashion" in channel_id.lower():
            category_bonus = 10
        elif "요리" in channel_id or "cooking" in channel_id.lower():
            category_bonus = 12
        
        adjusted_score = max(0, min(100, base_score + positive_bonus - negative_penalty + comment_bonus + category_bonus))
        
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
        """
        ROI 추정 계산
        """
        
        # 1. 예상 조회수: 실제 데이터(avg_views)가 있으면 우선 사용, 없으면 추정
        if avg_views > 0:
            estimated_views = avg_views
        else:
            # 데이터 없을 때만 추정
            if subscriber_count > 1000000:
                estimated_views = int(subscriber_count * 0.15)
            elif subscriber_count > 100000:
                estimated_views = int(subscriber_count * 0.20)
            elif subscriber_count > 10000:
                estimated_views = int(subscriber_count * 0.25)
            else:
                estimated_views = int(subscriber_count * 0.30)
        
        # 2. 예상 비용 계산 
        if subscriber_count < 10000:
            cost_per_10k_subs = 5
        elif subscriber_count < 100000:
            cost_per_10k_subs = 8
        elif subscriber_count < 1000000:
            cost_per_10k_subs = 12
        else:
            cost_per_10k_subs = 20
            
        estimated_cost_value = (subscriber_count / 10000) * cost_per_10k_subs * 10000
        estimated_cost = self._format_cost(estimated_cost_value)
        
        # 총합 100점 만점 구성
        # 1. 참여율 (60점 만점) - 핵심 지표
        # 2. 가성비/효율 (20점 만점) - 구독자 대비 조회수
        # 3. 규모 점수 (20점 만점) - 구독자 수 (Log Scale)
        # ---------------------------------------------------------

        # 1. 참여율 점수 (Max 60점)
        # 참여율 15% 이상이면 만점, 그 아래는 비례 점수
        # 예: 7.5% -> 30점, 15% -> 60점
        target_engagement = 15.0
        engagement_score = min(60, (engagement_rate / target_engagement) * 60)

        # 2. 조회수 효율 점수 (Max 20점)
        # 구독자 대비 조회수가 50% 이상이면 만점
        view_ratio = estimated_views / max(1, subscriber_count)
        target_ratio = 0.5 # 50%
        view_ratio_score = min(20, (view_ratio / target_ratio) * 20)

        # 3. 규모 점수 (Max 20점)
        # 구독자 100만명 이상이면 만점, 로그 스케일 적용 (작은 채널도 점수 확보 가능)
        # math.log10을 사용하여 1만~100만 사이를 부드럽게 연결
        import math
        if subscriber_count <= 1000:
            subscriber_score = 0
        else:
            # 3~6 사이의 값을 0~20점으로 매핑
            log_subs = math.log10(subscriber_count)
            subscriber_score = min(20, max(0, (log_subs - 3) / (6 - 3) * 20))

        roi_score = engagement_score + view_ratio_score + subscriber_score
        
        # 예상 참여율 (단순 표시용)
        estimated_engagement = min(engagement_rate * 1.1, 10.0)

        return ROIEstimate(
            score=round(roi_score, 2),
            estimated_views=estimated_views,
            estimated_engagement=round(estimated_engagement, 2),
            estimated_cost=estimated_cost,
            cpm=cost_per_10k_subs
        )
    
    def calculate_total_score(
        self,
        brand_score: float,
        sentiment_score: float,
        roi_score: float,
        weights: WeightConfig
    ) -> TotalScore:
        """종합 점수 계산"""
        
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
        
        return TotalScore(
            total_score=round(total_score, 2),
            grade="B",
            recommendation="분석 중..",
            weights_used=weights
        )
    def apply_relative_distribution(self, results: List[TotalScore]) -> List[TotalScore]:
        """ 49명 전체 데이터를 받아 S~D 등급으로 강제 배분"""
        import math

        if not results:
            return []

        # 1. 원점수(raw_score) 기준 1등부터 꼴등까지 정렬
        # 점수가 높은 순서대로 줄을 세웁니다.
        sorted_results = sorted(results, key=lambda x: x.total_score, reverse=True)
        
        total_count = len(sorted_results)
        final_results = []

        # 2. 목표 점수 범위 설정 (92점 ~ 53점)
        MAX_SCORE = 92.0
        MIN_SCORE = 53.0

        for rank, item in enumerate(sorted_results):
            # 상위 몇 %인지 계산 (0.0 = 1등, 1.0 = 꼴등)
            percentile = rank / max(1, total_count - 1)

            # [S-Curve 보정] 상위권/하위권 변별력 강화, 중위권은 두텁게
            # 코사인 함수를 써서 부드러운 곡선으로 점수를 배분합니다.
            curve_factor = (math.cos(percentile * math.pi) + 1) / 2
            
            # 최종 점수 확정
            final_score = MIN_SCORE + (curve_factor * (MAX_SCORE - MIN_SCORE))
            
            # 확정된 점수로 등급과 추천사 다시 계산
            new_grade = self._calculate_grade(final_score)
            new_recommendation = self._generate_recommendation(final_score, new_grade)

            # 결과 업데이트
            # Pydantic 모델의 불변성(immutable)을 고려해 새로 생성
            updated_item = TotalScore(
                total_score=round(final_score, 2),
                grade=new_grade,
                recommendation=new_recommendation,
                weights_used=item.weights_used
            )
            final_results.append(updated_item)

        return final_results
    
    def _normalize_score(self, score: float, min_val: float, max_val: float) -> float:
        """점수를 0-100 범위로 정규화"""
        if max_val == min_val:
            return 50.0
        normalized = ((score - min_val) / (max_val - min_val)) * 100
        return max(0, min(100, normalized))
    
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
