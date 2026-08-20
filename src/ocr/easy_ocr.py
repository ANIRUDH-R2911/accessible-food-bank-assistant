import easyocr

ocr = easyocr.Reader(["en"], gpu=False)

def extract_text(image_path):
    result = ocr.readtext(image_path, detail=1)
    lines = []
    for item in result:
        text = item[1]
        confidence = item[2]
        lines.append(f"{text} | conf={confidence:.2f}")
    return "\n".join(lines)