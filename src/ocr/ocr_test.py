import easyocr

print("Loading OCR model...")

reader = easyocr.Reader(['en'])

print("Reading image...")

results = reader.readtext("data/raw_images/3.jpg")

print("\nDetected Text:\n")

for bbox, text, confidence in results:
    print(f"Text: {text}")
    print(f"Confidence: {confidence:.2f}")
    print("-" * 40)