class SessionQueryLimiter:
    def __init__(self, max_queries=3):
        if not isinstance(max_queries, int) or isinstance(max_queries, bool):
            raise TypeError("max queries must be an integer.")
        if max_queries < 1:
            raise ValueError("max queries must be at least 1.")

        self.max_queries = max_queries
        self._query_count = 0

    @property
    def query_count(self):
        return self._query_count

    @property
    def remaining_queries(self):
        return max(0, self.max_queries - self._query_count)

    def allow_query(self):
        if self._query_count >= self.max_queries:
            return False
        self._query_count += 1
        return True

    def reset(self):
        self._query_count = 0

    def execute_query(self, query_function, *args, **kwargs):
        if not self.allow_query():
            return (
                f"You've reached the limit of {self.max_queries} queries "
                "for this session. Please start a new session to continue."
            )
        return query_function(*args, **kwargs)
