from pydantic import BaseModel, Field
from typing import Optional, List

# 요청 스키마
class BrandCompatibilityRequest(BaseModel):
    channel_id: str = Field(..., description="채널 ID")
    brand_name: str = Field(..., description="브랜드/제품 이름")
    brand_description: str = Field(..., description="제품 설명")
    brand_tone: str = Field(..., description="브랜드 톤앤매너")
    brand_category: str = Field(..., description="브랜드 카테고리")
    brand_image_url: Optional[str] = Field(None, description="제품 이미지 URL")
    brand_image_base64: Optional[str] = Field(None, description="제품 이미지 Base64")

class WeightConfig(BaseModel):
    brand_image_weight: float = Field(0.3, ge=0, le=1)
    sentiment_weight: float = Field(0.3, ge=0, le=1)
    roi_weight: float = Field(0.4, ge=0, le=1)

class SimulatorRequest(BaseModel):
    channel_id: str = Field(..., description="채널 ID")
    brand_name: str = Field(..., description="브랜드 이름")
    brand_description: str = Field(..., description="제품 설명")
    brand_tone: str = Field(..., description="브랜드 톤앤매너")
    brand_category: str = Field(..., description="브랜드 카테고리")
    brand_image_url: Optional[str] = None
    brand_image_base64: Optional[str] = None
    weights: Optional[WeightConfig] = None

# 응답 스키마
class BrandImageScore(BaseModel):
    score: float = Field(..., description="브랜드 이미지 적합도 점수 (0-100)")
    details: dict = Field(..., description="상세 분석 결과")

class SentimentScore(BaseModel):
    score: float = Field(..., description="감성분석 점수 (0-100)")
    positive_ratio: float = Field(..., description="긍정 비율")
    negative_ratio: float = Field(..., description="부정 비율")
    neutral_ratio: float = Field(..., description="중립 비율")
    total_comments: int = Field(..., description="분석된 댓글 수")

class ROIEstimate(BaseModel):
    score: float = Field(..., description="ROI 점수 (0-100)")
    estimated_views: int = Field(..., description="예상 조회수")
    estimated_engagement: float = Field(..., description="예상 참여율")
    estimated_cost: str = Field(..., description="예상 비용")
    cpm: float = Field(..., description="예상 CPM")

class TotalScore(BaseModel):
    total_score: float = Field(..., description="종합 점수 (0-100)")
    grade: str = Field(..., description="등급 (S, A, B, C, D)")
    recommendation: str = Field(..., description="추천 사유")
    weights_used: WeightConfig = Field(..., description="사용된 가중치")

class SimulatorResponse(BaseModel):
    channel_id: str
    brand_name: str
    brand_image: BrandImageScore
    sentiment: SentimentScore
    roi: ROIEstimate
    total: TotalScore
