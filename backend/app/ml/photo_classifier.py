"""
Photo-based disease classification.
Phase 1: EfficientNet-B4 fine-tuned on veterinary skin/eye datasets.
Phase 2: YOLOv8 for lesion detection + classification.

Datasets:
- HuggingFace: karenwky/pet-health-symptoms-dataset
- GitHub: kvinicki/Veterinary-image-datasets
- Kaggle: various pet dermatology datasets
"""

from typing import Optional
import io


class PhotoClassifier:
    """CV model for pet skin/eye disease classification."""

    def __init__(self, model_path: Optional[str] = None):
        self.model = None
        self.labels = [
            "healthy",
            "dermatitis",
            "fungal_infection",
            "ear_infection",
            "eye_infection",
            "flea_allergy",
            "hotspot",
            "mange",
            "tumor",
            "wound",
        ]

    async def load_model(self, model_path: str):
        """Load EfficientNet-B4 weights."""
        # TODO: load PyTorch/ONNX model
        # import torch
        # from torchvision.models import efficientnet_b4
        # self.model = efficientnet_b4(pretrained=False)
        # self.model.load_state_dict(torch.load(model_path))
        # self.model.eval()
        pass

    async def predict(self, image_bytes: bytes) -> dict:
        """
        Run inference on pet photo.
        Returns: {"condition": str, "confidence": float, "severity": str}
        """
        # TODO: preprocess image (resize, normalize)
        # TODO: run model inference
        # TODO: map output to condition + confidence

        # Placeholder
        return {
            "condition": "dermatitis",
            "confidence": 0.87,
            "severity": "medium",
            "description": "Обнаружены признаки аллергического дерматита",
            "recommendation": "Рекомендуется визит к ветеринару-дерматологу",
            "should_visit_vet": True,
        }


# Singleton
classifier = PhotoClassifier()
