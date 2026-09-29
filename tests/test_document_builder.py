import sys
from pathlib import Path
from pprint import pprint

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.rag.document_builder import DocumentBuilder

def main():
    builder = DocumentBuilder()
    sample_item = {
        "item_id": "FBA-123",
        "ingredients": [
            "milk",
            "sugar",
            "cocoa"
        ],
        "contains_allergens": [
            "milk"
        ],
        "nutrition": {
            "calories": 120,
            "protein": 8,
            "fat": 4
        }
    }

    result = builder.build_document(sample_item)
    print("\n----- DOCUMENT OBJECT -----\n")
    pprint(result)
    print("\n----- DOCUMENT TEXT -----\n")
    print(result["document"])
    print("\n----- METADATA -----\n")
    pprint(result["metadata"])

if __name__ == "__main__":
    main()