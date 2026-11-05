from src.Inventory.inventory_manager import InventoryManager
from src.rag.document_builder import DocumentBuilder
from src.rag.chroma_manager import ChromaManager

class InventoryIndexer:
    def __init__(self, inventory_manager=None, document_builder=None, chroma_manager=None):
        self.inventory_manager = inventory_manager or InventoryManager()
        self.document_builder = document_builder or DocumentBuilder()
        self.chroma_manager = chroma_manager or ChromaManager()

    def synchronize(self):
        inventory_items = self.inventory_manager.get_all_items()
        if not isinstance(inventory_items, list):
            raise ValueError("Inventory data must be a list.")

        built_documents = self.document_builder.build_documents(inventory_items)
        if not isinstance(built_documents, list):
            raise ValueError("DocumentBuilder must return a list.")
        if len(built_documents) != len(inventory_items):
            raise ValueError("DocumentBuilder output count does not match inventory count. Synchronization stopped.")

        desired = {}
        for entry in built_documents:
            if not isinstance(entry, dict):
                raise ValueError("Invalid document builder output.")

            item_id = entry.get("id")
            document = entry.get("document")
            metadata = entry.get("metadata")
            if not isinstance(item_id, str) or not item_id.strip():
                raise ValueError("Every indexed document must have a valid ID.")
            if item_id in desired:
                raise ValueError(f"Duplicate document ID found: {item_id}")
            if not isinstance(document, str) or not document.strip():
                raise ValueError(f"Document content is missing for item: {item_id}")
            if not isinstance(metadata, dict):
                raise ValueError(f"Invalid metadata for item: {item_id}")
            desired[item_id] = {
                "document": document,
                "metadata": metadata,
            }

        existing = self.chroma_manager.get_all_documents()
        if not isinstance(existing, dict):
            raise ValueError("Invalid ChromaDB response.")

        existing_ids = existing.get("ids")
        existing_documents = existing.get("documents")
        existing_metadatas = existing.get("metadatas")
        if not all(
            isinstance(values, list)
            for values in (
                existing_ids,
                existing_documents,
                existing_metadatas,
            )
        ):
            raise ValueError(
                "ChromaDB returned invalid record arrays."
            )

        if not (len(existing_ids) == len(existing_documents) == len(existing_metadatas)):
            raise ValueError("ChromaDB record arrays have inconsistent lengths. Synchronization stopped.")

        for item_id, document, metadata in zip(existing_ids, existing_documents, existing_metadatas):
            if (not isinstance(item_id, str) or not isinstance(document, str) or not isinstance(metadata, dict)):
                raise ValueError("ChromaDB contains an invalid record. Synchronization stopped.")

        if len(existing_ids) != len(set(existing_ids)):
            raise ValueError("ChromaDB contains duplicate document IDs.")
        existing_by_id = {
            item_id: {
                "document": document,
                "metadata": metadata,
            }
            for item_id, document, metadata in zip(existing_ids, existing_documents, existing_metadatas)
        }

        if not desired and existing_ids:
            raise ValueError("Source inventory is empty but ChromaDB contains records. Synchronization stopped to prevent accidental deletion.")

        new_ids = []
        updated_ids = []
        skipped_count = 0
        ids_to_upsert = []
        documents_to_upsert = []
        metadatas_to_upsert = []
        for item_id, record in desired.items():
            existing_record = existing_by_id.get(item_id)
            if existing_record is None:
                new_ids.append(item_id)
            elif (existing_record["document"] == record["document"] and existing_record["metadata"] == record["metadata"]):
                skipped_count += 1
                continue
            else:
                updated_ids.append(item_id)

            ids_to_upsert.append(item_id)
            documents_to_upsert.append(record["document"])
            metadatas_to_upsert.append(record["metadata"])

        stale_ids = [
            item_id
            for item_id in existing_ids
            if item_id not in desired
        ]
        if ids_to_upsert:
            self.chroma_manager.add_documents(ids=ids_to_upsert, documents=documents_to_upsert, metadatas=metadatas_to_upsert)
        if stale_ids:
            self.chroma_manager.delete_documents(stale_ids)
        return {
            "inventory_count": len(inventory_items),
            "indexed_count": len(desired),
            "added": len(new_ids),
            "updated": len(updated_ids),
            "removed": len(stale_ids),
            "skipped": skipped_count,
        }
