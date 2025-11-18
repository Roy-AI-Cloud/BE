"""
CLIP 기반 이미지 유사도 분석
"""
import torch
from PIL import Image
import requests
from io import BytesIO
import base64
from typing import List, Optional
from .model_manager import model_manager

def load_image_from_url(url: str) -> Optional[Image.Image]:
    """URL에서 이미지 로드"""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        image = Image.open(BytesIO(response.content)).convert("RGB")
        return image
    except Exception as e:
        print(f"[Error] 이미지 로드 실패 ({url}): {e}")
        return None

def load_image_from_base64(base64_str: str) -> Optional[Image.Image]:
    """Base64 문자열에서 이미지 로드"""
    try:
        image_data = base64.b64decode(base64_str)
        image = Image.open(BytesIO(image_data)).convert("RGB")
        return image
    except Exception as e:
        print(f"[Error] Base64 이미지 로드 실패: {e}")
        return None

def calculate_image_similarity(
    brand_image: Image.Image,
    channel_thumbnails: List[Image.Image]
) -> float:
    """CLIP 모델을 사용한 이미지 유사도 계산"""
    if not channel_thumbnails:
        return 50.0
    
    try:
        clip_model, clip_processor = model_manager.get_clip_model()
        device = model_manager.device
        
        # 브랜드 이미지 임베딩
        brand_inputs = clip_processor(images=brand_image, return_tensors="pt").to(device)
        with torch.no_grad():
            brand_features = clip_model.get_image_features(**brand_inputs)
            brand_features = brand_features / brand_features.norm(dim=-1, keepdim=True)
        
        # 채널 썸네일 임베딩 및 유사도 계산
        similarities = []
        for thumbnail in channel_thumbnails:
            thumb_inputs = clip_processor(images=thumbnail, return_tensors="pt").to(device)
            with torch.no_grad():
                thumb_features = clip_model.get_image_features(**thumb_inputs)
                thumb_features = thumb_features / thumb_features.norm(dim=-1, keepdim=True)
                
                # 코사인 유사도 계산
                similarity = torch.cosine_similarity(brand_features, thumb_features).item()
                similarities.append(similarity)
        
        # 평균 유사도를 0-100 스케일로 변환
        avg_similarity = sum(similarities) / len(similarities)
        return max(0, min(100, (avg_similarity + 1) * 50))
        
    except Exception as e:
        print(f"[Error] CLIP 유사도 계산 실패: {e}")
        return 50.0

def calculate_text_image_similarity(text: str, images: List[Image.Image]) -> float:
    """텍스트와 이미지 간 CLIP 유사도 계산"""
    if not images:
        return 50.0
    
    try:
        clip_model, clip_processor = model_manager.get_clip_model()
        device = model_manager.device
        
        # 텍스트 임베딩
        text_inputs = clip_processor(text=[text], return_tensors="pt").to(device)
        with torch.no_grad():
            text_features = clip_model.get_text_features(**text_inputs)
            text_features = text_features / text_features.norm(dim=-1, keepdim=True)
        
        # 이미지들과의 유사도 계산
        similarities = []
        for image in images:
            image_inputs = clip_processor(images=image, return_tensors="pt").to(device)
            with torch.no_grad():
                image_features = clip_model.get_image_features(**image_inputs)
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)
                
                similarity = torch.cosine_similarity(text_features, image_features).item()
                similarities.append(similarity)
        
        avg_similarity = sum(similarities) / len(similarities)
        return max(0, min(100, (avg_similarity + 1) * 50))
        
    except Exception as e:
        print(f"[Error] 텍스트-이미지 유사도 계산 실패: {e}")
        return 50.0
