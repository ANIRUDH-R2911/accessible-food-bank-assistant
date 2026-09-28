import time

from src.services.search_service import SearchService
from src.conversation.response_formatter import (ResponseFormatter)
from src.conversation.conversation_logger import (ConversationLogger)


class ConversationService:
    def __init__(self):
        self.search_service = SearchService()
        self.response_formatter = ResponseFormatter()
        self.logger = ConversationLogger()

    def ask(self, question):
        if not question or not question.strip():
            return "Please enter a food search query."
        start_time = time.perf_counter()
        try:
            results = self.search_service.search(question)
            response = (self.response_formatter.format_response(question, results))
            latency = (time.perf_counter() - start_time)
            self.logger.log_interaction(query=question, result_count=len(results), latency_seconds=latency)
            return response

        except Exception as e:
            latency = (time.perf_counter() - start_time)
            self.logger.log_interaction(query=question, result_count=0, latency_seconds=latency)
            return ("An error occurred while processing your request.")