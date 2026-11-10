class SessionQueryLimiter:
    def __init__(self, max_generations=3):
        if not isinstance(max_generations, int) or isinstance(max_generations, bool):
            raise TypeError("max generations must be an integer.")
        if max_generations < 1:
            raise ValueError("max generations must be at least 1.")

        self.max_generations = max_generations
        self._generation_count = 0

    @property
    def generation_count(self):
        return self._generation_count

    @property
    def remaining_generations(self):
        return max(0, self.max_generations - self._generation_count)

    def can_generate(self):
        return self._generation_count < self.max_generations
    
    def record_generation_attempt(self):
        if not self.can_generate():
            return False
        self._generation_count+=1
        return True
    
    def reset(self):
        self._generation_count = 0
