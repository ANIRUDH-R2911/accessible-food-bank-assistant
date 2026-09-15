import json
import os
import re
import time
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("GEMINI_API_KEY not found")

MODEL_NAME = "gemini-3.6-flash"
IMAGE_DIR = Path("data/evaluation_images")
OUTPUT_PATH = Path("data/results/gemini_3.6_full_predictions.json")
BATCH_SIZE = 5

client = genai.Client(api_key=API_KEY)

BATCH_PROMPT = """
You are analyzing multiple packaged food labels.

For each provided image, extract ONLY information visible in that specific image.

Tasks for each image:
1. Extract all ingredients.
2. Extract allergens explicitly listed in a Contains statement.
3. Extract allergens explicitly listed in a May Contain, Processed in Facility, or similar precautionary statement.
4. Extract nutrition facts.

Rules:
- Return a JSON array containing one object per image.
- Match each result to its corresponding image filename provided in the prompt context.
- Do not infer ingredients or allergens.
- Return null for missing fields.
- One ingredient per list item; expand grouped ingredients whenever visible.

Schema:
[
    {
        "image_name": "<filename>",
        "ingredients": [],
        "contains_allergens": [],
        "may_contain": [],
        "nutrition": {
            "calories": null,
            "total_fat": null,
            "saturated_fat": null,
            "trans_fat": null,
            "cholesterol": null,
            "sodium": null,
            "total_carbohydrate": null,
            "dietary_fiber": null,
            "total_sugars": null,
            "added_sugars": null,
            "protein": null,
            "vitamin_d": null,
            "calcium": null,
            "iron": null,
            "potassium": null
            }
    }
]
"""


def load_existing_results():
    if not OUTPUT_PATH.exists():
        return []
    try:
        with open(OUTPUT_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_results(results):
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)


def print_candidate_diagnostics(response, batch_names):
    print(f"\n[DIAGNOSTIC] Empty response text for batch: {batch_names}")
    if hasattr(response, "prompt_feedback") and response.prompt_feedback:
        print(f"Prompt Feedback: {response.prompt_feedback}")
    if getattr(response, "candidates", None):
        for idx, candidate in enumerate(response.candidates):
            print(
                f"Candidate {idx} Finish Reason: {getattr(candidate, 'finish_reason', 'N/A')}"
            )
            print(
                f"Candidate {idx} Safety Ratings: {getattr(candidate, 'safety_ratings', 'N/A')}"
            )


def generate_batch_prediction(image_paths):
    contents = [BATCH_PROMPT]

    for img_path in image_paths:
        contents.append(f"\nImage File: {img_path.name}")
        contents.append(Image.open(img_path))

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=contents,
        config=types.GenerateContentConfig(
            response_mime_type="application/json"
        ),
    )

    if not response or not response.text:
        print_candidate_diagnostics(response, [p.name for p in image_paths])
        return ""

    return response.text


def parse_response_text(raw_text):
    if not raw_text or not raw_text.strip():
        raise ValueError("Received empty or invalid response string from API")

    clean_text = raw_text.strip()
    clean_text = re.sub(r"^```json\s*", "", clean_text)
    clean_text = re.sub(r"^```\s*", "", clean_text)
    clean_text = re.sub(r"\s*```$", "", clean_text)

    return json.loads(clean_text)


def process_single_file(img_file):
    single_response = client.models.generate_content(
        model=MODEL_NAME,
        contents=[
            BATCH_PROMPT,
            f"Image File: {img_file.name}",
            Image.open(img_file),
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json"
        ),
    )

    if not single_response or not single_response.text:
        print_candidate_diagnostics(single_response, [img_file.name])
        raise ValueError("API returned empty text (Likely Safety/Filter block)")

    single_parsed = parse_response_text(single_response.text)
    if isinstance(single_parsed, list):
        single_parsed = single_parsed[0]

    return {
        "image_name": img_file.name,
        "ingredients": single_parsed.get("ingredients", []),
        "contains_allergens": single_parsed.get("contains_allergens", []),
        "may_contain": single_parsed.get("may_contain", []),
        "nutrition": single_parsed.get("nutrition", {}),
        "raw_response": single_response.text,
    }


def main():
    print("\n" + "-" * 60)
    print("GEMINI BATCH BENCHMARK GENERATION")
    print("-" * 60)

    image_files = sorted(
        [
            f
            for f in IMAGE_DIR.iterdir()
            if f.suffix.lower() in [".jpg", ".jpeg", ".png"]
        ]
    )

    existing_results = load_existing_results()
    processed_images = {
        item["image_name"]
        for item in existing_results
        if item.get("image_name")
    }

    unprocessed_files = [
        f for f in image_files if f.name not in processed_images
    ]

    print(f"\nTotal Images Found: {len(image_files)}")
    print(f"Already Processed: {len(processed_images)}")
    print(f"Remaining to Process: {len(unprocessed_files)}")

    results = existing_results

    for i in range(0, len(unprocessed_files), BATCH_SIZE):
        batch = unprocessed_files[i : i + BATCH_SIZE]
        batch_names = [f.name for f in batch]

        print(
            f"\n[Batch {i // BATCH_SIZE + 1}/{(len(unprocessed_files) + BATCH_SIZE - 1) // BATCH_SIZE}] "
            f"Processing: {', '.join(batch_names)}"
        )

        try:
            raw_response = generate_batch_prediction(batch)
            parsed_batch = parse_response_text(raw_response)

            if isinstance(parsed_batch, dict):
                parsed_batch = [parsed_batch]

            for item in parsed_batch:
                result = {
                    "image_name": item.get("image_name"),
                    "ingredients": item.get("ingredients", []),
                    "contains_allergens": item.get("contains_allergens", []),
                    "may_contain": item.get("may_contain", []),
                    "nutrition": item.get("nutrition", {}),
                    "raw_response": raw_response,
                }
                results.append(result)

            save_results(results)
            print("SUCCESS: Batch processed and saved.")
            time.sleep(2)

        except Exception as batch_error:
            print(f"\n[BATCH FAILED]: {batch_error}")
            print(
                "Isolating batch files to locate failing image and recover valid ones..."
            )

            for img_file in batch:
                try:
                    res = process_single_file(img_file)
                    results.append(res)
                    save_results(results)
                    print(
                        f"  --> [SINGLE OK]: {img_file.name} successfully extracted."
                    )
                except Exception as single_error:
                    print(
                        f"  --> [CULPRIT FOUND]: {img_file.name} FAILED! Reason: {single_error}"
                    )
                    results.append(
                        {
                            "image_name": img_file.name,
                            "error": str(single_error),
                            "ingredients": [],
                            "contains_allergens": [],
                            "may_contain": [],
                            "nutrition": {},
                        }
                    )
                    save_results(results)

    print("\n" + "-" * 60)
    print("COMPLETE")
    print("-" * 60)
    print(f"\nSaved Results:\n{OUTPUT_PATH}")
    print(f"Total Images Processed: {len(results)}")


if __name__ == "__main__":
    main()