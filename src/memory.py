"""
memory.py — Stores behavioral fingerprints (weekly vectors + detection results) per
entity, so drift can be explained against real history, not just the current window.
Tries Qdrant (real deployment target) first. Falls back to a local JSON store if
Qdrant isn't configured/reachable 
"""

import os
import json
import uuid
from pathlib import Path

LOCAL_STORE_PATH = Path(__file__).parent.parent / "data" / "local_memory.json"


class LocalMemory:
    """Zero-dependency fallback: one JSON file, one array of records per entity."""

    def __init__(self, path=LOCAL_STORE_PATH):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("{}")

    def _load(self):
        return json.loads(self.path.read_text())

    def _save(self, data):
        self.path.write_text(json.dumps(data, indent=2))

    def store_fingerprint(self, entity_id: str, week: str, vector: list, detection_result: dict):
        data = self._load()
        data.setdefault(entity_id, [])
        data[entity_id] = [r for r in data[entity_id] if r["week"] != week]  # upsert
        data[entity_id].append({
            "id": str(uuid.uuid4()),
            "week": week,
            "vector": list(vector),
            "detection_result": detection_result,
        })
        data[entity_id].sort(key=lambda r: r["week"])
        self._save(data)

    def get_history(self, entity_id: str):
        return self._load().get(entity_id, [])


class QdrantMemory:

    def __init__(self, collection_name="behaviordrift_fingerprints", vector_size=4):
        from qdrant_client import QdrantClient
        from qdrant_client.models import Distance, VectorParams

        url = os.environ["QDRANT_URL"]
        api_key = os.environ.get("QDRANT_API_KEY")
        self.client = QdrantClient(url=url, api_key=api_key)
        self.collection_name = collection_name

        existing = [c.name for c in self.client.get_collections().collections]
        if collection_name not in existing:
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
            )

    def store_fingerprint(self, entity_id: str, week: str, vector: list, detection_result: dict):
        from qdrant_client.models import PointStruct
        point_id = str(uuid.uuid4())
        self.client.upsert(
            collection_name=self.collection_name,
            points=[PointStruct(
                id=point_id,
                vector=list(vector),
                payload={"entity_id": entity_id, "week": week, "detection_result": detection_result},
            )],
        )

    def get_history(self, entity_id: str):
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        results, _ = self.client.scroll(
            collection_name=self.collection_name,
            scroll_filter=Filter(must=[FieldCondition(key="entity_id", match=MatchValue(value=entity_id))]),
            limit=1000,
        )
        records = [{"week": r.payload["week"], "vector": r.vector,
                    "detection_result": r.payload["detection_result"]} for r in results]
        return sorted(records, key=lambda r: r["week"])


def get_memory_backend():
    """Auto-selects Qdrant if configured, otherwise local JSON fallback."""
    if os.environ.get("QDRANT_URL"):
        try:
            return QdrantMemory()
        except Exception as e:
            print(f"[memory] Qdrant configured but connection failed ({e}); falling back to local store.")
    return LocalMemory()


if __name__ == "__main__":
    mem = get_memory_backend()
    mem.store_fingerprint("octocat/demo", "2026-W20", [40, 1, 6, 40.0], {"status": "flagged"})
    print(mem.get_history("octocat/demo"))
