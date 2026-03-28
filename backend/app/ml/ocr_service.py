"""
OCR service for lab results extraction.
Supports: PaddleOCR (default), Tesseract (fallback).
"""

from typing import Optional


class OCRService:
    """Extract text from lab results photos/PDFs."""

    def __init__(self, engine: str = "paddleocr"):
        self.engine = engine
        self.ocr = None

    async def initialize(self):
        """Load OCR engine."""
        if self.engine == "paddleocr":
            # from paddleocr import PaddleOCR
            # self.ocr = PaddleOCR(use_angle_cls=True, lang='ru')
            pass
        elif self.engine == "tesseract":
            # import pytesseract
            pass

    async def extract_text(self, image_bytes: bytes) -> str:
        """
        Extract text from image of lab results.
        Returns raw text string.
        """
        # TODO: run OCR
        # if self.engine == "paddleocr":
        #     result = self.ocr.ocr(image_bytes, cls=True)
        #     lines = [line[1][0] for block in result for line in block]
        #     return "\n".join(lines)

        # Placeholder
        return "Гемоглобин: 145 г/л\nЛейкоциты: 12.5 x10⁹/л\nЭритроциты: 7.2 x10¹²/л"


# Singleton
ocr_service = OCRService()
