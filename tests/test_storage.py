import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.storage.inventory_manager import InventoryManager

manager = InventoryManager()

sample_product = {
    "product_name": "Honey Nut Cheerios",
    "ingredients": [
        "Whole Grain Oats",
        "Sugar",
        "Salt"
    ],
    "allergens": [
        "Wheat"
    ],
    "nutrition": {
        "Sodium": "180mg",
        "Protein": "5g"
    }
}

saved_record = manager.add_product(sample_product)
print(saved_record)