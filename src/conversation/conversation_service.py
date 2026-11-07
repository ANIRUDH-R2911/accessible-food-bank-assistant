import time
import os 

from src.services.search_service import SearchService
from src.conversation.response_formatter import ResponseFormatter
from src.conversation.conversation_logger import ConversationLogger
from src.rag.answer_generator import AnswerGenerator
from src.services.daily_generation_budget import DailyGenerationBudget
from src.rag.answer_validator import AnswerValidator

class AnswerValidationError(Exception):
    """Raised when a generated answer fails inventory evidence validation."""

class ConversationService:
    def __init__(self, search_service=None, response_formatter=None, logger=None, answer_generator=None, generation_budget=None,):
        self.search_service = search_service or SearchService()
        self.response_formatter = response_formatter or ResponseFormatter()
        self.logger = logger or ConversationLogger()
        self.answer_generator = answer_generator
        self.generation_budget = (
            generation_budget
            if generation_budget is not None
            else DailyGenerationBudget()
            )
        self.answer_validator = AnswerValidator()
        self.last_search_results = []

    def ask(self, question):
        self.last_search_results = []
        if not isinstance(question, str) or not question.strip():
            return "Please enter a food search query."
        start_time = time.perf_counter()
        results = []
        answer_generation_status = "not_attempted"
        generation_latency_seconds = None
        generation_attempts = 0
        error_type = None
        try:
            results = self.search_service.search(question)
            self.last_search_results = results
            if not results:
                response = self.response_formatter.format_response(question, results)
            elif os.getenv("GEMINI_ANSWER_GENERATION_ENABLED", "false").lower() != "true":
                response = self.response_formatter.format_response(question, results)
                answer_generation_status = "disabled"
            else:
                generation_start = time.perf_counter()
                try:
                    response = self.generate_answer(question, results)
                    if not self.answer_validator.validate(response, results):
                        raise AnswerValidationError("Generated answer failed inventory evidence validation.")
                    if self.answer_generator is not None:
                        generation_attempts = int(getattr(self.answer_generator, "last_model_call_attempted", False))
                    answer_generation_status = "success"
                except Exception as exc:
                    response = self.response_formatter.format_response(question, results)
                    error_type = type(exc).__name__
                    if isinstance(exc, AnswerValidationError):
                        answer_generation_status = "validation_failed"
                    elif str(exc) == "Daily Gemini generation budget exhausted.":
                        answer_generation_status = "budget_exhausted"
                    else:
                        answer_generation_status = "fallback"
                finally:
                    generation_latency_seconds = time.perf_counter() - generation_start
                    if self.answer_generator is not None:
                        generation_attempts = int(getattr(self.answer_generator, "last_model_call_attempted", True))
        except Exception as exc:
            response = self.response_formatter.format_response(question, results)
            error_type = type(exc).__name__
        finally:
            latency = time.perf_counter() - start_time
            self.logger.log_interaction(
                query=question,
                result_count=len(results),
                latency_seconds=latency,
                answer_generation_status=answer_generation_status,
                generation_latency_seconds=generation_latency_seconds,
                generation_attempts=generation_attempts,
                error_type=error_type,
                )
        return response
    
    def generate_answer(self, question, results):
        if self.answer_generator is None:
            self.answer_generator = AnswerGenerator(generation_budget=self.generation_budget)
        return self.answer_generator.generate_answer(question, results)
