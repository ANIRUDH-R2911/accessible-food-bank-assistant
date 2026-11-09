import json
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.services.daily_generation_budget import DailyGenerationBudget
from src.rag.config import MAX_QUERY_LENGTH
from src.prompts.generation_prompt import (GENERATION_SYSTEM_INSTRUCTION, build_generation_prompt)

class AnswerGenerator:
    def __init__(self, client=None, model_name=None, generation_budget=None):
        self.generation_budget = (
            generation_budget
            if generation_budget is not None
            else DailyGenerationBudget()
            )
        self.model_name = (model_name or os.getenv("GEMINI_ANSWER_MODEL") or "gemini-3.5-flash-lite")
        self.last_model_call_attempted = False
        if client is not None:
            self.client = client
        else:
            load_dotenv()
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY not found in environment or .env file.")

            self.client = genai.Client(
                api_key=api_key,
                http_options=types.HttpOptions(
                    timeout=30_000,
                    retry_options=types.HttpRetryOptions(attempts=1),
                    ),
                )

    def generate_answer(self, question, records):
        if not isinstance(question, str):
            raise TypeError("Question must be a string.")
        if not question.strip():
            raise ValueError("Question cannot be empty.")
        if len(question) > MAX_QUERY_LENGTH:
            raise ValueError(f"Question exceeds the maximum allowed length of {MAX_QUERY_LENGTH} characters.")
        self.last_model_call_attempted = False
        if not question or not question.strip():
            return "Please enter a food search query."
        if not records:
            return (
                "I couldn't find any foods matching your request.\n\n"
                "Try searching by:\n"
                "- ingredient\n"
                "- allergen\n"
                "- nutrition"
            )

        evidence = self.build_evidence(records)
        if not json.loads(evidence):
            raise ValueError("No authoritative inventory records available for answer generation.")

        prompt = self.build_prompt(question, evidence)
        if not self.generation_budget.reserve():
            raise RuntimeError("Daily Gemini generation budget exhausted.")
        self.last_model_call_attempted = True
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(system_instruction=GENERATION_SYSTEM_INSTRUCTION, temperature=0.2),
            )
        answer = getattr(response, "text", None)
        if not isinstance(answer, str) or not answer.strip():
            raise ValueError("The answer model returned an empty response.")
        return answer.strip()

    def build_evidence(self, records):
        evidence = []
        for result in records:
            if not isinstance(result, dict):
                continue
            inventory_record = result.get("inventory_data")
            inventory_fields = {
                "ingredients",
                "contains_allergens",
                "may_contain",
                "nutrition",
            }
            if inventory_record is None and (inventory_fields.intersection(result)):
                inventory_record = result
            if not isinstance(inventory_record, dict):
                continue
            item_id = inventory_record.get("item_id")
            if not item_id:
                continue
            if isinstance(result.get("inventory_data"), dict):
                metadata = result.get("metadata")
                wrapper_ids = [
                    result.get("item_id"),
                    result.get("id"),
                    metadata.get("item_id") if isinstance(metadata, dict) else None,
                    ]
                if any(
                    wrapper_id is not None and str(wrapper_id) != str(item_id)
                    for wrapper_id in wrapper_ids
                    ):
                    continue
            entry = {
                "item_id": item_id,
                "ingredients": inventory_record.get("ingredients"),
                "contains_allergens": inventory_record.get(
                    "contains_allergens"
                ),
                "may_contain": inventory_record.get("may_contain"),
                "nutrition": inventory_record.get("nutrition"),
            }
            retrieval_context = {}
            for key in ("score", "distance", "rrf_score", "retriever"):
                if key in result:
                    retrieval_context[key] = result[key]
            if retrieval_context:
                entry["retrieval_context"] = retrieval_context
            evidence.append(entry)
        return json.dumps(evidence, ensure_ascii=False, default=str)
    
    def build_prompt(self, question, evidence):
        return build_generation_prompt(question, evidence)
