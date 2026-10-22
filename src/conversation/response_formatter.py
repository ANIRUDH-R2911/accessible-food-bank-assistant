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


        result_count = len(results)
        item_ids = []
        for result in results[: self.max_examples]:
            if not isinstance(result, dict):
                item_ids.append("UNKNOWN_ITEM")
                continue
            inventory_data = result.get("inventory_data")
            if not isinstance(inventory_data, dict):
                inventory_data = result
            item_id = (
                inventory_data.get("item_id")
                or result.get("item_id")
                or result.get("id")
                or (result.get("metadata") or {}).get("item_id")
                or "UNKNOWN_ITEM"
            )
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
