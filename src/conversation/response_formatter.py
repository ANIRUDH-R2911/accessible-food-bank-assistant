class ResponseFormatter:
    def __init__(self, max_examples=5):
        self.max_examples = max_examples

    def format_response(self, query, results):
        if not query or not query.strip():
            return "Please enter a food search query."

        if not results:
            return (
                "I couldn't find any foods matching your request.\n\n"
                "Try searching by:\n"
                "- ingredient\n"
                "- allergen\n"
                "- nutrition"
            )

        result_count = len(results) if results else 0
        item_ids = []
        for item in results[: self.max_examples]:
            item_id = item.get("item_id", "UNKNOWN_ITEM")
            item_ids.append(item_id)

        if result_count == 1:
            return (
                "I found 1 matching food.\n\n"
                f"Item ID:\n"
                f"- {item_ids[0]}"
            )

        response_lines = [
            f"I found {result_count} foods matching your request.",
            "",
            "Examples include:"
        ]

        for item_id in item_ids:
            response_lines.append(f"- {item_id}")

        if result_count > self.max_examples:
            remaining = result_count - self.max_examples
            response_lines.append("")
            response_lines.append(f"...and {remaining} more matching items.")

        return "\n".join(response_lines)