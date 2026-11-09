import os
import json
import uuid
import sys
from pathlib import Path
from mimetypes import guess_type
from dotenv import load_dotenv
from google import genai
from google.genai import types
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.prompts.extraction_prompt import (EXTRACTION_SYSTEM_INSTRUCTION, build_extraction_prompt)
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

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=[
                build_extraction_prompt(),
                types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
                ],
            config=types.GenerateContentConfig(
                system_instruction=EXTRACTION_SYSTEM_INSTRUCTION,
                temperature=0.1,
                response_mime_type="application/json",
                ),
            )
        raw_text = response.text.strip()

        try:
            if raw_text.startswith("```json"):
                raw_text = (raw_text.replace("```json", "").replace("```", "").strip())
            result = json.loads(raw_text)
        except Exception as e:
            raise ValueError("Failed to parse Gemini JSON response.") from e

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