import csv
import json
import platform
import re
import shutil
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path
import chromadb
import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR / "datasets"
INDEX_ROOT = SCRIPT_DIR / "indexes"
RESULT_DIR = PROJECT_ROOT / "experiments" / "database_scaling" / "results"
JUDGMENTS_PATH = (PROJECT_ROOT / "data" / "results" / "retrieval_relevance_judgments.json")
TARGET_SIZES = [1000, 2500, 5000, 10000]
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
TOP_K = 5
RETRIEVAL_K = 20
RRF_K = 60
WARMUP_RUNS = 3
BENCHMARK_RUNS = 20
EMBEDDING_BATCH_SIZE = 64
CHROMA_BATCH_SIZE = 500
RANDOM_SEED = 42

def build_bm25_document(item):
    ingredients = item.get("ingredients", [])
    allergens = item.get("contains_allergens", [])
    nutrition = item.get("nutrition", {})
    document_parts = []
    if ingredients:
        document_parts.extend(ingredients)
    if allergens:
        document_parts.extend(allergens)
    for nutrient, value in nutrition.items():
        document_parts.append(str(nutrient))
        document_parts.append(str(value))
    return " ".join(document_parts)

def safe_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None

def build_semantic_document(item):
    item_id = item.get("item_id", "UNKNOWN")
    ingredients = item.get("ingredients", [])
    allergens = item.get("contains_allergens", [])
    nutrition = item.get("nutrition", {})
    lines = [
        f"Item ID: {item_id}", "",
        "Ingredients:", ", ".join(ingredients) if ingredients else "None", "",
        "Allergens:", ", ".join(allergens) if allergens else "None", "",
        "Nutrition:",
    ]
    if nutrition:
        for nutrient, value in nutrition.items():
            lines.append(f"{nutrient}: {value}")
    else:
        lines.append("None")
    descriptions = []
    protein = safe_float(nutrition.get("protein"))
    calories = safe_float(nutrition.get("calories"))
    if protein is not None:
        if protein >= 15:
            descriptions.append("This food is a high protein food.")
        elif protein >= 8:
            descriptions.append("This food is a moderate protein food.")
        else:
            descriptions.append("This food is a low protein food.")
    if calories is not None:
        if calories >= 300:
            descriptions.append("This food is high in calories.")
        elif calories <= 120:
            descriptions.append("This food is lower in calories.")
    if allergens:
        descriptions.append("This food contains allergens.")
        for allergen in allergens:
            descriptions.append(f"This food contains {allergen}.")
    else:
        descriptions.append("No allergens were detected.")
    if descriptions:
        lines.extend(["", "Food Characteristics:"])
        lines.extend(descriptions)
    return "\n".join(lines)

def tokenize(text):
    return re.findall(r"\b[a-zA-Z0-9]+\b", text.lower())

def load_dataset(target_size):
    path = DATA_DIR / f"synthetic_inventory_{target_size}.json"
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)
    items = data.get("items")
    if not isinstance(items, list):
        raise ValueError(f"Invalid dataset format: {path}")
    if len(items) != target_size:
        raise ValueError(f"Expected {target_size} records, found {len(items)}")
    ids = [item.get("item_id") for item in items]
    if None in ids or len(ids) != len(set(ids)):
        raise ValueError(f"Missing or duplicate item IDs in {path}")
    return items

class SyntheticBM25:
    def __init__(self, items):
        start = time.perf_counter()
        self.documents = []
        for item in items:
            self.documents.append({
                "id": item["item_id"],
                "document": build_bm25_document(item),
            })
        self.corpus = [
            tokenize(document["document"])
            for document in self.documents
        ]
        self.bm25 = BM25Okapi(self.corpus)
        self.build_time_ms = (time.perf_counter() - start) * 1000

    def search(self, query, top_k=TOP_K):
        scores = self.bm25.get_scores(tokenize(query))
        ranked_indices = sorted(range(len(scores)), key=lambda index: scores[index], reverse=True)
        return [
            {
                "id": self.documents[index]["id"],
                "score": float(scores[index]),
            }
            for index in ranked_indices[:top_k]
        ]

class SyntheticSemantic:
    def __init__(self, items, model, target_size):
        self.model = model
        self.index_path = INDEX_ROOT / f"chroma_{target_size}"
        if self.index_path.exists():
            shutil.rmtree(self.index_path)
        self.index_path.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=str(self.index_path))
        self.collection = self.client.get_or_create_collection(name="synthetic_inventory")
        documents = [
            build_semantic_document(item)
            for item in items
        ]
        ids = [
            item["item_id"]
            for item in items
        ]
        metadatas = [
            {
                "item_id": item["item_id"],
                "ingredient_count": len(item.get("ingredients", [])),
                "allergen_count": len(item.get("contains_allergens", [])),
            }
            for item in items
        ]
        embedding_start = time.perf_counter()
        embeddings = self.model.encode(
            documents,
            batch_size=EMBEDDING_BATCH_SIZE,
            convert_to_numpy=True,
            show_progress_bar=True,
        )
        self.embedding_time_ms = (time.perf_counter() - embedding_start) * 1000
        add_start = time.perf_counter()
        for start in range(0, len(ids), CHROMA_BATCH_SIZE):
            end = start + CHROMA_BATCH_SIZE
            self.collection.add(
                ids=ids[start:end],
                documents=documents[start:end],
                metadatas=metadatas[start:end],
                embeddings=embeddings[start:end].tolist(),
            )
        self.chroma_add_time_ms = (time.perf_counter() - add_start) * 1000
        self.build_time_ms = (self.embedding_time_ms + self.chroma_add_time_ms)

    def search(self, query, top_k=TOP_K):
        query_embedding = self.model.encode(query, convert_to_numpy=True)
        results = self.collection.query(query_embeddings=[query_embedding.tolist()], n_results=top_k)
        ids = results["ids"][0]
        return [{"id": item_id} for item_id in ids]

def reciprocal_rank_fusion(bm25_results, semantic_results):
    fused_scores = {}
    for rank, result in enumerate(bm25_results, start=1):
        item_id = result["id"]
        fused_scores[item_id] = (fused_scores.get(item_id, 0) + 1 / (RRF_K + rank))
    for rank, result in enumerate(semantic_results, start=1):
        item_id = result["id"]
        fused_scores[item_id] = (fused_scores.get(item_id, 0) + 1 / (RRF_K + rank))
    ranked = sorted(fused_scores.items(), key=lambda entry: entry[1], reverse=True)
    return [
        {"id": item_id, "rrf_score": score}
        for item_id, score in ranked
    ]

def load_judgments():
    if not JUDGMENTS_PATH.exists():
        raise FileNotFoundError(f"Judgments file not found: {JUDGMENTS_PATH}")
    with JUDGMENTS_PATH.open("r", encoding="utf-8") as file:
        data = json.load(file)
    queries = []
    for entry in data.get("queries", []):
        if entry.get("review_status") != "completed":
            continue
        judgments = entry.get("relevance_judgments", {})
        reviewed = {
            item_id: grade
            for item_id, grade in judgments.items()
            if grade in (0, 1, 2)
        }
        if reviewed:
            queries.append({
                "query": entry["query"],
                "judgments": reviewed,
            })
    return queries

def evaluate_judged_results(results, judgments):
    retrieved_ids = [result["id"] for result in results[:TOP_K]]
    judged_results = [
        judgments[item_id]
        for item_id in retrieved_ids
        if item_id in judgments
    ]
    relevant_ids = {
        item_id
        for item_id, grade in judgments.items()
        if grade == 2
    }
    retrieved_relevant = sum(
        1
        for item_id in retrieved_ids
        if judgments.get(item_id) == 2
    )
    judged_count = len(judged_results)
    return {
        "judged_precision": (
            sum(grade == 2 for grade in judged_results) / judged_count
            if judged_count else None
        ),
        "judgment_coverage": judged_count / TOP_K,
        "relevant_recall": (
            retrieved_relevant / len(relevant_ids)
            if relevant_ids else None
        ),
        "judged_results": judged_count,
        "unjudged_results": TOP_K - judged_count,
    }

def percentile(values, percentile_value):
    return float(np.percentile(values, percentile_value))

def latency_summary(values):
    return {
        "average_ms": statistics.mean(values),
        "median_ms": statistics.median(values),
        "p95_ms": percentile(values, 95),
        "max_ms": max(values),
    }

def measure_search(search_function, query):
    for _ in range(WARMUP_RUNS):
        search_function(query)
    measurements = []
    for _ in range(BENCHMARK_RUNS):
        start = time.perf_counter()
        search_function(query)
        measurements.append((time.perf_counter() - start) * 1000)
    return measurements

def directory_size(path):
    total = 0
    for file in path.rglob("*"):
        if file.is_file():
            total += file.stat().st_size
    return total


def main():
    np.random.seed(RANDOM_SEED)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    INDEX_ROOT.mkdir(parents=True, exist_ok=True)
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    queries = load_judgments()
    print("-" * 50)
    print("SYNTHETIC DATABASE SCALING BENCHMARK")
    print("-" * 50)
    print("Datasets:", TARGET_SIZES)
    print("Judged queries:", len(queries))
    print("Warmup runs:", WARMUP_RUNS)
    print("Measured runs:", BENCHMARK_RUNS)
    print("Embedding model:", EMBEDDING_MODEL_NAME)
    print("\nLoading embedding model...")
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    all_results = []
    for target_size in TARGET_SIZES:
        print("\n" + "=" * 65)
        print(f"DATASET SIZE: {target_size:,}")
        print("=" * 65)
        items = load_dataset(target_size)
        print(f"Loaded {len(items):,} records.")
        print("\nBuilding BM25 index...")
        bm25 = SyntheticBM25(items)
        print(f"BM25 build: {bm25.build_time_ms:.2f} ms")
        print("\nBuilding isolated semantic index...")
        semantic = SyntheticSemantic(items=items, model=model, target_size=target_size)
        print(f"Embedding generation: {semantic.embedding_time_ms:.2f} ms")
        print(f"ChromaDB insertion: {semantic.chroma_add_time_ms:.2f} ms")
        print(f"Semantic build total: {semantic.build_time_ms:.2f} ms")
        dataset_storage_bytes = directory_size(semantic.index_path)
        for query_entry in queries:
            query = query_entry["query"]
            judgments = query_entry["judgments"]
            print(f"\nQuery: {query}")
            bm25_latency = measure_search(lambda q: bm25.search(q, TOP_K), query)
            bm25_results = bm25.search(query, TOP_K)
            semantic_latency = measure_search(lambda q: semantic.search(q, TOP_K), query)
            semantic_results = semantic.search(query, TOP_K)

            def hybrid_search(q):
                lexical = bm25.search(q, RETRIEVAL_K)
                vector = semantic.search(q, RETRIEVAL_K)
                return reciprocal_rank_fusion(lexical, vector)[:TOP_K]

            hybrid_latency = measure_search(hybrid_search, query)
            hybrid_results = hybrid_search(query)
            methods = {
                "bm25": (bm25_latency, bm25_results),
                "semantic": (semantic_latency, semantic_results),
                "hybrid": (hybrid_latency, hybrid_results),
            }
            for method, (latencies, results) in methods.items():
                quality = evaluate_judged_results(results, judgments)
                entry = {
                    "dataset_size": target_size,
                    "query": query,
                    "method": method,
                    **latency_summary(latencies),
                    **quality,
                    "top_5_ids": [result["id"] for result in results[:TOP_K]],
                }
                all_results.append(entry)
                print(
                    f"{method.upper():8s} | "
                    f"avg: {entry['average_ms']:.3f} ms | "
                    f"p95: {entry['p95_ms']:.3f} ms | "
                    f"judgment coverage: "
                    f"{entry['judgment_coverage']:.0%}"
                )
        print(f"\nChromaDB storage: {dataset_storage_bytes / (1024 * 1024):.2f} MB")
        for entry in all_results:
            if entry["dataset_size"] == target_size:
                entry["bm25_build_ms"] = bm25.build_time_ms
                entry["semantic_build_ms"] = semantic.build_time_ms
                entry["embedding_generation_ms"] = semantic.embedding_time_ms
                entry["chroma_insertion_ms"] = semantic.chroma_add_time_ms
                entry["chroma_storage_bytes"] = dataset_storage_bytes

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    json_path = (RESULT_DIR / f"database_scaling_report_{timestamp}.json")
    csv_path = (RESULT_DIR / f"database_scaling_report_{timestamp}.csv")
    report = {
        "benchmark": "synthetic_database_scaling",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "embedding_model": EMBEDDING_MODEL_NAME,
        "dataset_sizes": TARGET_SIZES,
        "top_k": TOP_K,
        "retrieval_k": RETRIEVAL_K,
        "rrf_k": RRF_K,
        "warmup_runs": WARMUP_RUNS,
        "benchmark_runs": BENCHMARK_RUNS,
        "query_count": len(queries),
        "results": all_results,
        "methodology_notes": [
            "All ChromaDB indexes are isolated under experiments/database_scaling/indexes.",
            "Production ChromaDB and inventory files are not accessed.",
            "BM25 uses the production BM25 document representation and tokenizer.",
            "Semantic documents mirror the uploaded production DocumentBuilder.",
            "Hybrid retrieval uses BM25, semantic retrieval, and RRF with k=60.",
            "Gemini answer generation is not included.",
            "Synthetic records have no independent human relevance judgments.",
            "Judged precision is calculated only among retrieved records with human labels.",
            "Judgment coverage is reported to expose unjudged retrieved records.",
            "Recall measures retrieval of the original human-labeled relevant item IDs.",
            "Synthetic data copies source records and varies nutrition values, so it is not a collection of independent real products.",
            "Query latency includes semantic query embedding generation.",
            "Results represent local benchmark performance, not Streamlit Cloud performance.",
        ],
    }
    with json_path.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=2)
    csv_fields = [
        "dataset_size",
        "query",
        "method",
        "average_ms",
        "median_ms",
        "p95_ms",
        "max_ms",
        "judged_precision",
        "judgment_coverage",
        "relevant_recall",
        "judged_results",
        "unjudged_results",
        "bm25_build_ms",
        "semantic_build_ms",
        "embedding_generation_ms",
        "chroma_insertion_ms",
        "chroma_storage_bytes",
    ]

    with csv_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=csv_fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(all_results)

    print("\n" + "-" * 50)
    print("BENCHMARK COMPLETED")
    print("-" * 50)
    print("JSON report:", json_path)
    print("CSV report:", csv_path)

if __name__ == "__main__":
    main()
