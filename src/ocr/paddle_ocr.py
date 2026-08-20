from paddleocr import PaddleOCR

ocr = PaddleOCR(lang="en")
def extract_text(image_path):
    result = ocr.ocr(image_path)
    lines = []
    for page in result:
        texts = page["rec_texts"]
        for text in texts:
            lines.append(text)
    return "\n".join(lines)