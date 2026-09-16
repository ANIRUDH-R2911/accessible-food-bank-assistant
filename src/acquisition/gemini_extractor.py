import os
import json
import uuid
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from mimetypes import guess_type
from google.genai import types


class GeminiExtractor:
    def __init__(self):
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in .env file")

        self.client = genai.Client(api_key=api_key)
        self.model_name = "gemini-3.5-flash-lite"

    def generate_item_id(self) -> str:
        return f"FBA-{uuid.uuid4().hex[:8].upper()}"

    def build_prompt(self) -> str:
        return """
    You are an expert food inventory extraction system.
    Analyze the food product image and extract information.
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
    1. Return only JSON.
    2. Do not include markdown.
    3. Do not include explanations.
    4. Ingredients must be a list of strings.
    5. Allergens must be a list of strings.
    6. Nutrition values must be numeric when visible.
    7. Use null if a nutrition value is not visible.
    8. If ingredients are unreadable return an empty list.
    """

    def extract(self, image_path: str) -> dict:
        image_path = Path(image_path)

        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        with open(image_path, "rb") as f:
            image_bytes = f.read()

        mime_type, _ = guess_type(str(image_path))
        if mime_type is None:
            mime_type = "image/jpeg"
        
        response = self.client.models.generate_content(model=self.model_name, contents=[self.build_prompt(), types.Part.from_bytes(data=image_bytes, mime_type=mime_type)])
        raw_text = response.text.strip()
        print("\n------ GEMINI RAW RESPONSE -------\n")
        print(raw_text)
        print("\n-----------\n")
        try:
            if raw_text.startswith("```json"):
                raw_text = raw_text.replace("```json","").replace("```","").strip()
            result = json.loads(raw_text)

        except Exception as e:
            raise ValueError(f"Failed to parse Gemini JSON response.\n\n" f"Response:\n{raw_text}") from e

        final_record = {
            "item_id": self.generate_item_id(),
            "ingredients": result.get("ingredients", []),
            "contains_allergens": result.get("contains_allergens", []),
            "may_contain": result.get("may_contain", []),
            "nutrition": result.get("nutrition", {})
        }
        return final_record


if __name__ == "__main__":
    extractor = GeminiExtractor()
    result = extractor.extract("data/evaluation_images/almond_milk.jpg")
    print(json.dumps(result, indent=4))