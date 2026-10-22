import json
import os
from dotenv import load_dotenv
from google import genai

class AnswerGenerator:
    def __init__(self, client=None, model_name=None):
        self.model_name = (model_name or os.getenv("GEMINI_ANSWER_MODEL") or "gemini-3.5-flash-lite")
        if client is not None:
            self.client = client
        else:
            load_dotenv()
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY not found in environment or .env file.")

            self.client = genai.Client(api_key=api_key)

    def generate_answer(self, question, records):
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
        response = self.client.models.generate_content(model=self.model_name, contents=prompt)
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
            for key in ("document", "score", "distance", "rrf_score", "retriever"):
                if key in result:
                    retrieval_context[key] = result[key]
            if retrieval_context:
                entry["retrieval_context"] = retrieval_context
            evidence.append(entry)
        return json.dumps(evidence, ensure_ascii=False, default=str)

    def build_prompt(self, question, evidence):
        return f"""
    You are an assistant for a food bank inventory.
    Answer the user's question using only the inventory evidence below.
    USER QUESTION:
    {question}
    RETRIEVED INVENTORY EVIDENCE (JSON):
    {evidence}
    Rules:
    1. Treat the retrieved records as the only source of product-specific facts.
    2. Never invent ingredients, nutrition values, allergens, quantities, or product details.
    3. Preserve item IDs when referring to individual foods.
    4. If a field is missing, null, or empty, explain that the information is unavailable in the inventory when relevant. Do not infer that the product lacks that ingredient or nutrient.
    5. An empty or missing contains_allergens list does not prove that a food is allergen-free or medically safe.
    6. Distinguish contains_allergens from may_contain. Do not merge these categories or omit relevant uncertainty.
    7. Never claim that a food is safe for someone with an allergy based only on these records. Recommend checking the product label and consulting appropriate food-bank staff when needed.
    8. If the evidence cannot answer the question, say so clearly.
    9. Be concise, helpful, and specific. Do not mention facts unsupported by the retrieved evidence.
    """.strip()
