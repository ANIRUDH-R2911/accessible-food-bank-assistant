import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.storage.inventory_manager import InventoryManager

manager = InventoryManager()

print("\nALL PRODUCTS")
print("-" * 40)

products = manager.get_all_products()
for product in products:
    print(product["product_name"])

print("\nSEARCH BY NAME")
print("-" * 40)

results = manager.search_by_name("cheerios")
for product in results:
    print(product["product_name"])

print("\nSEARCH BY INGREDIENT")
print("-" * 40)

results = manager.search_by_ingredient("oats")
for product in results:
    print(product["product_name"])

print("\nSEARCH BY ALLERGEN")
print("-" * 40)

results = manager.search_by_allergen("wheat")
for product in results:
    print(product["product_name"])