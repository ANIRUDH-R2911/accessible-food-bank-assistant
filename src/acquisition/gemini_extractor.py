import os
import json
import uuid
from pathlib import Path
from mimetypes import guess_type

from dotenv import load_dotenv
from google import genai
from google.genai import types
class GeminiExtractor:
    def __init__(self, model_name: str = "gemini-3.5-flash-lite"):
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in .env file")
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name

    def generate_item_id(self) -> str:
        return f"FBA-{uuid.uuid4().hex[:8].upper()}"

    def build_prompt(self) -> str:
        return """
    You are an expert food inventory extraction system.
    Analyze the provided food product image and extract all visible food inventory information.
    Return ONLY valid JSON.
    Schema:
    {
        "ingredients": [],
        "contains_allergens": [],
        "may_contain": [],
        "nutrition": {
            "calories": null,
            "fat_g": null,
            "carbohydrates_g": null,
            "protein_g": null,
            "sodium_mg": null,
            "sugar_g": null
            }
    }
    Rules:
    1. Return JSON only.
    2. Do not include markdown.
    3. Do not include explanations.
    4. Ingredients must be a list of strings.
    5. Allergens must be a list of strings.
    6. Nutrition values must be numeric when visible.
    7. Use null when information is not visible.
    8. If ingredients cannot be read, return an empty list.
    9. Extract only information visible in the image.
    10. Do not hallucinate ingredients or nutrition values.
"""

    def extract(self, image_path: str) -> dict:
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")
        print(f"[INFO] Using model: " f"{self.model_name}")
        with open(image_path, "rb") as f:
            image_bytes = f.read()
        mime_type, _ = guess_type(str(image_path))
        if mime_type is None:
            mime_type = "image/jpeg"

        response = self.client.models.generate_content(model=self.model_name, contents=[self.build_prompt(), types.Part.from_bytes(data=image_bytes, mime_type=mime_type)])
        raw_text = response.text.strip()

        print("\n------ GEMINI RAW RESPONSE ------\n")
        print(raw_text)
        print("\n---------------------------------\n")

        try:
            if raw_text.startswith("```json"):
                raw_text = (raw_text.replace("```json", "").replace("```", "").strip())
            result = json.loads(raw_text)
        except Exception as e:
            raise ValueError("Failed to parse Gemini JSON response.\n\n" f"Response:\n{raw_text}") from e

        final_record = {
            "item_id": self.generate_item_id(),
            "ingredients": result.get("ingredients", []),
            "contains_allergens": result.get("contains_allergens", []),
            "may_contain": result.get("may_contain", []),
            "nutrition": result.get("nutrition", {})
        }
        return final_record

if __name__ == "__main__":
    ...