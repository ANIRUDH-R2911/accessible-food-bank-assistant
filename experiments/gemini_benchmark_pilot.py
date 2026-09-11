import os
import json
import time
from dotenv import load_dotenv
from pathlib import Path
from PIL import Image
from google import genai

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

MODEL_NAME = "gemini-3.6-flash"

IMAGE_DIR = Path("data/evaluation_images")

OUTPUT_PATH = Path("data/results/gemini_pilot_predictions.json")

TEST_IMAGES = [
    "Sports_drink.jpg",
    "m&m.jpg",
    "mac_n_cheese.jpg",
]

client = genai.Client(api_key=API_KEY)

PROMPT = """
You are extracting ingredients from a packaged food label.

Task:
Extract ALL ingredients visible in the image.

Rules:
- Return ingredients only.
- Do not return nutrition facts.
- Do not return marketing text.
- Expand grouped ingredients into individual ingredients whenever possible.
- Return one ingredient per list entry.
- Preserve ingredient wording exactly when visible.

Return ONLY valid JSON.

Schema:

{
    "ingredients": []
}
"""

def extract_ingredients(image_path):
    image = Image.open(image_path)
    response = client.models.generate_content(model=MODEL_NAME, contents=[image, PROMPT])
    return response.text

def main():
    results = []
    print("\n------ GEMINI PILOT ------\n")

    for image_name in TEST_IMAGES:
        image_path = IMAGE_DIR / image_name
        if not image_path.exists():
            print(f"Skipping: {image_name}")
            continue

        print(f"Processing: {image_name}")
        try:
            response_text = extract_ingredients(image_path)

            results.append({
                "image_name": image_name,
                "raw_response": response_text
            })

            print("Success")
            time.sleep(2)

        except Exception as e:
            print(f"Failed: {image_name}")
            results.append({
                "image_name": image_name,
                "error": str(e)
            })

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)

    print(f"\nSaved results to:\n{OUTPUT_PATH}")

if __name__ == "__main__":
    main()