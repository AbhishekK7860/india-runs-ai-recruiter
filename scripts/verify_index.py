"""Verify FAISS index integrity and run a sample semantic search."""
import json
import faiss
import numpy as np

print("=== FAISS Index Integrity Check ===")

index = faiss.read_index("data/index/faiss.index")
print(f"Vectors in index : {index.ntotal}")
print(f"Dimensions       : {index.d}")
print(f"Index type       : {type(index).__name__}")

with open("data/index/metadata.json") as f:
    meta = json.load(f)

next_id = meta.get("next_id", "N/A")
id_map = meta.get("id_to_candidate", {})
print(f"Metadata next_id : {next_id}")
print(f"ID map entries   : {len(id_map)}")
print(f"First entry      : 0 -> {id_map.get('0', 'N/A')}")
print(f"Last entry       : 99999 -> {id_map.get('99999', 'N/A')}")

assert index.ntotal == 100000, f"Expected 100000, got {index.ntotal}"
assert index.d == 384, f"Expected 384 dims, got {index.d}"
assert len(id_map) == 100000, f"Expected 100000 ID map entries, got {len(id_map)}"
print("\nAll count assertions passed.")

print("\n=== Sample Semantic Search ===")
from backend.embeddings.encoder import TextEncoder
encoder = TextEncoder(cache=None)
query_vec = encoder.encode(["Senior AI Engineer with Python LLMs and FAISS experience"])
scores, ids = index.search(query_vec, 5)
print("Query: 'Senior AI Engineer with Python LLMs and FAISS experience'")
for i, (cid, sc) in enumerate(zip(ids[0], scores[0])):
    raw_id = id_map.get(str(cid), "UNKNOWN")
    print(f"  #{i+1}: {raw_id} (score={sc:.4f})")

print("\nVerification complete. Index is operational.")
