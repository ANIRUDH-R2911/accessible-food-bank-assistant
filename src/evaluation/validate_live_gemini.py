import json
import logging
import os
import sys
from dotenv import load_dotenv

load_dotenv()

if not os.getenv("GEMINI_API_KEY"):
    raise RuntimeError("GEMINI_API_KEY is missing. Check your local .env configuration.")

os.environ["GEMINI_ANSWER_GENERATION_ENABLED"] = "true"
logging.basicConfig(level=logging.CRITICAL)

from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from src.services.search_service import SearchService
from src.conversation.conversation_service import ConversationService
from src.rag.answer_generator import AnswerGenerator

class RecordingSearchService:
    def __init__(self, search_service):
        self.search_service = search_service
        self.last_results = []

    def search(self, query):
        self.last_results = self.search_service.search(query)
        return self.last_results


class SilentLogger:
    def log_interaction(self, **kwargs):
        pass


class ObservedAnswerGenerator(AnswerGenerator):
    def __init__(self):
        super().__init__()
        self.attempts = 0
        self.last_error = None

    def generate_answer(self, question, records):
        self.attempts += 1
        self.last_error = None
        try:
            return super().generate_answer(question, records)
        except Exception as exc:
            self.last_error = f"{type(exc).__name__}: {exc}"
            raise


def main():
    search_service = RecordingSearchService(SearchService())
    answer_generator = ObservedAnswerGenerator()
    conversation = ConversationService(search_service=search_service, answer_generator=answer_generator, logger=SilentLogger())
    queries = [
        "Find foods containing soy",
        "Find foods with more than 10g of protein",
        "Find foods with less than 1g of sugar",
    ]

    for number, query in enumerate(queries, start=1):
        print("\n" + "-" * 70)
        print(f"TEST {number}: {query}")
        print("-" * 70)
        previous_attempts = answer_generator.attempts
        try:
            answer = conversation.ask(query)
        except Exception as exc:
            print(f"APPLICATION ERROR: {type(exc).__name__}: {exc}")
            continue
        results = search_service.last_results
        print(f"\nRetrieved result count: {len(results)}")
        try:
            evidence = json.loads(answer_generator.build_evidence(results))
        except Exception as exc:
            evidence = []
            print(f"Could not inspect evidence: {type(exc).__name__}: {exc}")

        print(f"Usable inventory evidence count: {len(evidence)}")
        for record in evidence:
            print(
                json.dumps(
                    {
                        "item_id": record.get("item_id"),
                        "ingredients": record.get("ingredients"),
                        "contains_allergens": record.get("contains_allergens"),
                        "may_contain": record.get("may_contain"),
                        "nutrition": record.get("nutrition"),
                    },
                    ensure_ascii=False,
                    default=str,
                )
            )

        attempts_this_query = answer_generator.attempts - previous_attempts
        print(f"\nGemini generation attempts: {attempts_this_query}")
        if answer_generator.last_error:
            print(f"Gemini error: {answer_generator.last_error}")
        print("\nAPPLICATION RESPONSE:")
        print(answer)

if __name__ == "__main__":
    main()
