import time
import os 

from src.services.search_service import SearchService
from src.conversation.response_formatter import ResponseFormatter
from src.conversation.conversation_logger import ConversationLogger
from src.rag.answer_generator import AnswerGenerator


class ConversationService:
    def __init__(self, search_service=None, response_formatter=None, logger=None, answer_generator=None):
        self.search_service = search_service or SearchService()
        self.response_formatter = response_formatter or ResponseFormatter()
        self.logger = logger or ConversationLogger()
        self.answer_generator = answer_generator

    def ask(self, question):
        if not question or not question.strip():
            return "Please enter a food search query."
        start_time = time.perf_counter()
        results = []
        try:
            results = self.search_service.search(question)
            if not results:
                response = (self.response_formatter.format_response(question, results))
            elif os.getenv("GEMINI_ANSWER_GENERATION_ENABLED", "false").lower() == "true":
                response = self.generate_answer(question, results)
            else:
                response = self.response_formatter.format_response(question, results)
        except Exception:
            response = self.response_formatter.format_response(question, results)
        finally:
            latency = (time.perf_counter() - start_time)
            self.logger.log_interaction(query=question, result_count=len(results), latency_seconds=latency)
        
        return response
    
    def generate_answer(self, question, results):
        if self.answer_generator is None:
            self.answer_generator = AnswerGenerator()
        try:
            return self.answer_generator.generate_answer(question, results)
        except Exception:
            return self.response_formatter.format_response(question, results)
