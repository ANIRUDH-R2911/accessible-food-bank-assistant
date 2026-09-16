import cv2
from paddleocr import PaddleOCR

class PaddleOCREngine:
    def __init__(self):
        self.ocr = PaddleOCR(lang="en")

    def readtext(self, image):
        if len(image.shape) == 2:
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        
        result = self.ocr.ocr(image)
        lines = []
        for page in result:
            texts = page["rec_texts"]
            
            for text in texts:
                lines.append((None, text, 1.0))
                
        return lines