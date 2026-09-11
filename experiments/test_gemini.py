from dotenv import load_dotenv
import os

from google import genai
from PIL import Image

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env file")

IMAGE_PATH = r"data/evaluation_images/Sports_drink.jpg"

MODEL_NAME = "gemini-3.6-flash"

client = genai.Client(api_key=API_KEY)


image = Image.open(IMAGE_PATH)


prompt = """
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

{"ingredients": []}
"""

print("\n===== SENDING REQUEST =====\n")

response = client.models.generate_content(model=MODEL_NAME, contents=[image, prompt])

print("\n===== GEMINI RESPONSE =====\n")
print(response.text)