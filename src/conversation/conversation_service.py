import time
import os 
from dotenv import load_dotenv
from src.services.search_service import SearchService
from src.services.session_query_limiter import SessionQueryLimiter
from src.conversation.response_formatter import ResponseFormatter
from src.conversation.conversation_logger import ConversationLogger
from src.rag.answer_generator import AnswerGenerator
from src.services.daily_generation_budget import DailyGenerationBudget
from src.rag.answer_validator import AnswerValidator
load_dotenv()
class AnswerValidationError(Exception):
    """Raised when a generated answer fails inventory evidence validation."""

class ConversationService:
    def __init__(self, search_service=None, response_formatter=None, logger=None, answer_generator=None, generation_budget=None, session_generation_limiter=None):
        self.search_service = search_service or SearchService()
        self.response_formatter = response_formatter or ResponseFormatter()
        self.logger = logger or ConversationLogger()
        self.answer_generator = answer_generator
        self.generation_budget = (
            generation_budget
            if generation_budget is not None
            else DailyGenerationBudget()
            )
        self.session_generation_limiter = session_generation_limiter
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
            elif (self.session_generation_limiter is not None and not self.session_generation_limiter.can_generate()):
                response = self.response_formatter.format_response(question, results)
                answer_generation_status = "session_limit_reached"
            else:
                generation_start = time.perf_counter()
                try:
                    response = self.generate_answer(question, results)
                    if not self.answer_validator.validate(response, results):
                        raise AnswerValidationError("Generated answer failed inventory evidence validation.")
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
                    generator = self.answer_generator
                    model_call_attempted = (
                        bool(getattr(generator, "last_model_call_attempted", True))
                        if generator is not None
                        else False
                    )
                    if model_call_attempted:
                        generation_attempts = 1
                        if self.session_generation_limiter is not None:
                            self.session_generation_limiter.record_generation_attempt()
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
