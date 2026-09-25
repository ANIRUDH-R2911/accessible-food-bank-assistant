from typing import List, Dict
from datetime import datetime
import logging

from src.Inventory.inventory_retriever import InventoryRetriever
from src.Inventory.query_router import QueryRouter


class SearchService:
    def __init__(self, inventory_path: str = "data/inventory/inventory.json"):
        self.router = QueryRouter()
        self.retriever = InventoryRetriever(inventory_path)
        logging.basicConfig(
            filename="logs/search_service.log",
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s"
        )

    def search(self, query: str) -> List[Dict]:
        self._validate_query(query)
        route_info = self.router.route(query)
        query_type = route_info.get("query_type")
        filters = route_info.get("filters", {})
        results = self._execute_retrieval(query_type, filters)
        self._log_search(query, query_type, len(results))
        return results

    def _validate_query(self, query: str) -> None:
        if query is None:
            raise ValueError("Query cannot be None.")

        if not isinstance(query, str):
            raise TypeError("Query must be a string.")

        if not query.strip():
            raise ValueError("Query cannot be empty.")
        
    def _execute_retrieval(self, query_type: str, filters: dict):
        if query_type == "ingredient":
            return self.retriever.search_by_ingredient(filters["ingredient"])
        elif query_type == "allergen":
            return self.retriever.search_by_allergen(filters["allergen"])
        elif query_type == "nutrition":
            return self.retriever.search_by_nutrition(
                nutrient=filters["nutrient"],
                operator=filters["operator"],
                value=filters["value"]
            )
        elif query_type == "multi_filter":
            return self.retriever.search_by_multiple_filters(
                ingredients=filters.get("ingredients"),
                allergens=filters.get("allergens"),
                nutrition=filters.get("nutrition")
                )
        
        return []

    def _log_search(self, query: str, route_type: str, result_count: int) -> None:
        logging.info(f"Query='{query}' | " f"Route='{route_type}' | " f"Results={result_count}")