"""
브랜드 적합도 분석 서비스
"""
from typing import Optional, List
from PIL import Image
from app.ml import (
    load_image_from_url,
    load_image_from_base64,
    calculate_image_similarity,
    calculate_brand_channel_compatibility
)
from app.schemas.roi import BrandImageScore

class BrandService:
    """브랜드 분석 관련 서비스"""
    
    def analyze_brand_compatibility(
        self,
        channel_id: str,
        brand_name: str,
        brand_description: str,
        brand_tone: str,
        brand_category: str,
        brand_image_url: Optional[str] = None,
        brand_image_base64: Optional[str] = None,
        channel_description: str = "",
        channel_titles: List[str] = None,
        channel_thumbnails: List[Image.Image] = None
    ) -> BrandImageScore:
        """브랜드 적합도 종합 분석"""
        
        if channel_titles is None:
            channel_titles = []
        if channel_thumbnails is None:
            channel_thumbnails = []
        
        # 1. 이미지 유사도 분석
        image_score = 50.0
        if brand_image_url or brand_image_base64:
            brand_image = None
            if brand_image_url:
                brand_image = load_image_from_url(brand_image_url)
            elif brand_image_base64:
                brand_image = load_image_from_base64(brand_image_base64)
            
            if brand_image and channel_thumbnails:
                image_score = calculate_image_similarity(brand_image, channel_thumbnails)
        
        # 2. 텍스트 기반 적합도 분석
        text_score = calculate_brand_channel_compatibility(
            brand_description=brand_description,
            brand_tone=brand_tone,
            brand_category=brand_category,
            channel_description=channel_description,
            channel_titles=channel_titles
        )
        
        # 3. 종합 점수 계산 - 극단적 분포 생성
        base_score = (image_score * 0.4 + text_score * 0.6)
        
        # 4. 완벽 매칭 보너스 (최대 30점)
        perfect_match_bonus = 0
        if brand_category.lower() in channel_description.lower():
            perfect_match_bonus += 20
        if brand_tone.lower() in channel_description.lower():
            perfect_match_bonus += 10
        
        # 5. 부분 매칭 보너스 (최대 15점)
        partial_match_bonus = 0
        if any(brand_category.lower() in title.lower() for title in channel_titles):
            partial_match_bonus += 10
        if len(channel_thumbnails) >= 3:
            partial_match_bonus += 5
        
        # 6. 페널티 적용 (매칭이 전혀 없으면 감점)
        penalty = 0
        if not perfect_match_bonus and not partial_match_bonus:
            penalty = 20
        
        total_score = max(0, min(100, base_score + perfect_match_bonus + partial_match_bonus - penalty))
        
        # 4. 상세 분석 결과
        details = {
            "image_similarity": round(image_score, 2),
            "text_compatibility": round(text_score, 2),
            "brand_category": brand_category,
            "analysis_method": "CLIP + Sentence-BERT",
            "channel_data_points": {
                "thumbnails_analyzed": len(channel_thumbnails),
                "titles_analyzed": len(channel_titles),
                "has_brand_image": bool(brand_image_url or brand_image_base64)
            }
        }
        
        return BrandImageScore(
            score=float(total_score),
            details={
                "image_similarity": float(image_score),
                "text_compatibility": float(text_score),
                "brand_category": brand_category,
                "analysis_method": "CLIP + Sentence-BERT",
                "channel_data_points": {
                    "thumbnails_analyzed": len(channel_thumbnails),
                    "titles_analyzed": len(channel_titles),
                    "has_brand_image": bool(brand_image_url or brand_image_base64)
                }
            }
        )
    
    def get_compatibility_grade(self, score: float) -> str:
        """적합도 점수를 등급으로 변환"""
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
    
    def generate_recommendation(self, score: float, brand_category: str) -> str:
        """점수 기반 추천 메시지 생성"""
        grade = self.get_compatibility_grade(score)
        
        recommendations = {
            "S": f"{brand_category} 브랜드와 매우 높은 적합도를 보입니다. 강력히 추천합니다.",
            "A": f"{brand_category} 브랜드와 높은 적합도를 보입니다. 협업을 추천합니다.",
            "B": f"{brand_category} 브랜드와 양호한 적합도를 보입니다. 검토 후 협업 가능합니다.",
            "C": f"{brand_category} 브랜드와 보통 수준의 적합도입니다. 신중한 검토가 필요합니다.",
            "D": f"{brand_category} 브랜드와 낮은 적합도를 보입니다. 다른 인플루언서를 고려해보세요."
        }
        
        return recommendations.get(grade, "분석 결과를 확인해주세요.")

# 서비스 인스턴스
brand_service = BrandService()
