"""
AI 모델 관리자 - 싱글톤 패턴으로 모델 로딩 및 관리
"""
import torch
from transformers import CLIPProcessor, CLIPModel
from sentence_transformers import SentenceTransformer
from app.config import settings
from typing import Optional

class ModelManager:
    """AI 모델들을 싱글톤 패턴으로 관리"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._clip_model = None
            self._clip_processor = None
            self._sbert_model = None
            self._kobert_tokenizer = None
            self._kobert_model = None
            self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            self._initialized = True
    
    @property
    def device(self):
        return self._device
    
    def get_clip_model(self):
        """CLIP 모델 lazy loading"""
        if self._clip_model is None:
            print("[ModelManager] Loading CLIP model...")
            self._clip_model = CLIPModel.from_pretrained(settings.CLIP_MODEL_NAME)
            self._clip_processor = CLIPProcessor.from_pretrained(settings.CLIP_MODEL_NAME)
            self._clip_model = self._clip_model.to(self._device)
            self._clip_model.eval()
            print(f"[ModelManager] CLIP model loaded on {self._device}")
        return self._clip_model, self._clip_processor
    
    def get_sbert_model(self):
        """Sentence-BERT 모델 lazy loading"""
        if self._sbert_model is None:
            print("[ModelManager] Loading Sentence-BERT model...")
            self._sbert_model = SentenceTransformer(settings.SBERT_MODEL)
            print("[ModelManager] Sentence-BERT model loaded")
        return self._sbert_model
    
    def get_kobert_model(self):
        """KoBERT 모델 lazy loading"""
        if self._kobert_model is None:
            try:
                print("[ModelManager] Loading KoBERT model...")
                from transformers import AutoTokenizer, AutoModelForSequenceClassification
                self._kobert_tokenizer = AutoTokenizer.from_pretrained(settings.KOBERT_MODEL, trust_remote_code=True)
                # device_map 파라미터로 직접 디바이스 지정 (meta tensor 문제 해결)
                self._kobert_model = AutoModelForSequenceClassification.from_pretrained(
                    settings.KOBERT_MODEL, 
                    trust_remote_code=True,
                    device_map=str(self._device),
                    torch_dtype=torch.float32  # 명시적으로 float32 사용
                )
                self._kobert_model.eval()
                print(f"[ModelManager] KoBERT model loaded on {self._device}")
            except Exception as e:
                print(f"[ModelManager] KoBERT loading failed: {e}")
                return None, None
        return self._kobert_model, self._kobert_tokenizer

# 전역 인스턴스
model_manager = ModelManager()
