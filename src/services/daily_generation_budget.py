import os
import threading
from datetime import datetime, timezone

class DailyGenerationBudget:
    def __init__(self, daily_limit=None, today_provider=None):
        configured_limit = (
            daily_limit
            if daily_limit is not None
            else int(os.getenv("GEMINI_DAILY_GENERATION_LIMIT", "600"))
        )

        if configured_limit < 0:
            raise ValueError("daily_limit must be non-negative")

        self.daily_limit = configured_limit
        self._today_provider = today_provider or (lambda: datetime.now(timezone.utc).date())
        self._lock = threading.Lock()
        self._day = self._today_provider()
        self._reserved = 0

    def reset_if_new_day(self):
        current_day = self._today_provider()
        if current_day != self._day:
            self._day = current_day
            self._reserved = 0

    def reserve(self):
        with self._lock:
            self.reset_if_new_day()
            if self._reserved >= self.daily_limit:
                return False
            self._reserved += 1
            return True

    def remaining(self):
        with self._lock:
            self.reset_if_new_day()
            return self.daily_limit - self._reserved

    def reserved_today(self):
        with self._lock:
            self.reset_if_new_day()
            return self._reserved
