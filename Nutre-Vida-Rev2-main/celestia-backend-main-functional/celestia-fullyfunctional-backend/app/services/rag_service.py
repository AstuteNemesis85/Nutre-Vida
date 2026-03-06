"""
RAG (Retrieval-Augmented Generation) Service
Provides vector-based retrieval of nutrition knowledge, user meal history,
and conversation context using ChromaDB and Google embeddings.
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from sqlalchemy.orm import Session

from app.config import settings


class RAGService:
    """
    Manages ChromaDB vector stores for:
    1. Nutrition knowledge base (static, loaded once)
    2. User meal history (per-user, updated on meal log)
    3. Conversation memory (per-user, updated on chat)
    """

    _instance: Optional["RAGService"] = None
    _initialized: bool = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if RAGService._initialized:
            return
        RAGService._initialized = True

        # Resolve paths
        self._backend_dir = Path(__file__).resolve().parent.parent.parent
        self._chroma_dir = str(self._backend_dir / "chroma_db")
        self._knowledge_path = str(
            Path(__file__).resolve().parent.parent / "data" / "nutrition_knowledge.json"
        )

        # Google embedding model
        self._embeddings = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001",
            google_api_key=settings.google_api_key,
        )

        # ChromaDB persistent client
        self._client = chromadb.PersistentClient(
            path=self._chroma_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )

        # Collections
        self._nutrition_col: Optional[chromadb.Collection] = None
        self._meal_col: Optional[chromadb.Collection] = None
        self._convo_col: Optional[chromadb.Collection] = None

    # ------------------------------------------------------------------
    # Initialization helpers
    # ------------------------------------------------------------------

    def initialize(self) -> None:
        """Call once at app startup to index the nutrition knowledge base."""
        self._ensure_collections()
        self._index_nutrition_knowledge()
        print("[RAG] Initialization complete")

    def _ensure_collections(self) -> None:
        self._nutrition_col = self._client.get_or_create_collection(
            name="nutrition_knowledge",
            metadata={"hnsw:space": "cosine"},
        )
        self._meal_col = self._client.get_or_create_collection(
            name="user_meals",
            metadata={"hnsw:space": "cosine"},
        )
        self._convo_col = self._client.get_or_create_collection(
            name="conversation_memory",
            metadata={"hnsw:space": "cosine"},
        )

    # ------------------------------------------------------------------
    # 1. Nutrition knowledge base
    # ------------------------------------------------------------------

    def _index_nutrition_knowledge(self) -> None:
        """Load nutrition_knowledge.json into ChromaDB if not already indexed."""
        if self._nutrition_col is None:
            self._ensure_collections()

        # Skip if already populated
        if self._nutrition_col.count() > 0:
            print(f"[RAG] Nutrition KB already indexed ({self._nutrition_col.count()} docs)")
            return

        if not os.path.exists(self._knowledge_path):
            print(f"[RAG] Knowledge file not found at {self._knowledge_path}")
            return

        with open(self._knowledge_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        ids: List[str] = []
        documents: List[str] = []
        metadatas: List[Dict[str, Any]] = []

        for category, entries in data.get("categories", {}).items():
            for entry in entries:
                doc_id = entry["id"]
                text = f"{entry['title']}\n\n{entry['content']}"
                meta = {
                    "category": category,
                    "title": entry["title"],
                    "tags": ",".join(entry.get("tags", [])),
                }
                ids.append(doc_id)
                documents.append(text)
                metadatas.append(meta)

        if not documents:
            return

        # Embed in batches of 20 (API rate-limit friendly)
        batch_size = 20
        for i in range(0, len(documents), batch_size):
            batch_docs = documents[i : i + batch_size]
            batch_ids = ids[i : i + batch_size]
            batch_meta = metadatas[i : i + batch_size]

            embeddings = self._embeddings.embed_documents(batch_docs)

            self._nutrition_col.add(
                ids=batch_ids,
                documents=batch_docs,
                embeddings=embeddings,
                metadatas=batch_meta,
            )

        print(f"[RAG] Indexed {len(documents)} nutrition knowledge entries")

    def retrieve_nutrition_knowledge(
        self, query: str, top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant nutrition knowledge for a query."""
        if self._nutrition_col is None or self._nutrition_col.count() == 0:
            return []

        try:
            query_embedding = self._embeddings.embed_query(query)
            results = self._nutrition_col.query(
                query_embeddings=[query_embedding],
                n_results=min(top_k, self._nutrition_col.count()),
                include=["documents", "metadatas", "distances"],
            )

            docs = []
            for idx in range(len(results["ids"][0])):
                docs.append(
                    {
                        "id": results["ids"][0][idx],
                        "content": results["documents"][0][idx],
                        "metadata": results["metadatas"][0][idx],
                        "relevance_score": 1 - results["distances"][0][idx],  # cosine → similarity
                    }
                )
            return docs

        except Exception as e:
            print(f"[RAG] Error retrieving nutrition knowledge: {e}")
            return []

    # ------------------------------------------------------------------
    # 2. User meal history
    # ------------------------------------------------------------------

    def index_user_meal(self, user_id: int, meal_data: Dict[str, Any]) -> None:
        """Index a single meal into the user_meals collection."""
        if self._meal_col is None:
            self._ensure_collections()

        try:
            meal_id = f"meal_{user_id}_{meal_data.get('id', datetime.now().timestamp())}"

            # Build a textual representation
            foods = []
            for item in meal_data.get("analysis_data", {}).get("items", []):
                name = (
                    item.get("name")
                    or item.get("food_name")
                    or item.get("item_name")
                    or "unknown"
                )
                foods.append(name)

            nutrition = meal_data.get("nutrition_summary", {})
            text = (
                f"Meal on {meal_data.get('upload_date', 'unknown date')} "
                f"({meal_data.get('meal_type', 'meal')}): "
                f"{', '.join(foods) if foods else 'food items'}. "
                f"Calories: {nutrition.get('total_calories', 'N/A')}, "
                f"Protein: {nutrition.get('total_protein', 'N/A')}g, "
                f"Carbs: {nutrition.get('total_carbs', 'N/A')}g, "
                f"Fat: {nutrition.get('total_fat', 'N/A')}g."
            )

            embedding = self._embeddings.embed_query(text)

            self._meal_col.upsert(
                ids=[meal_id],
                documents=[text],
                embeddings=[embedding],
                metadatas=[
                    {
                        "user_id": str(user_id),
                        "meal_type": meal_data.get("meal_type", "unknown"),
                        "upload_date": str(meal_data.get("upload_date", "")),
                        "calories": str(nutrition.get("total_calories", 0)),
                    }
                ],
            )
        except Exception as e:
            print(f"[RAG] Error indexing meal for user {user_id}: {e}")

    def retrieve_user_meals(
        self, user_id: int, query: str, top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant meals for a user based on a query."""
        if self._meal_col is None or self._meal_col.count() == 0:
            return []

        try:
            query_embedding = self._embeddings.embed_query(query)
            results = self._meal_col.query(
                query_embeddings=[query_embedding],
                n_results=min(top_k, self._meal_col.count()),
                where={"user_id": str(user_id)},
                include=["documents", "metadatas", "distances"],
            )

            docs = []
            for idx in range(len(results["ids"][0])):
                docs.append(
                    {
                        "id": results["ids"][0][idx],
                        "content": results["documents"][0][idx],
                        "metadata": results["metadatas"][0][idx],
                        "relevance_score": 1 - results["distances"][0][idx],
                    }
                )
            return docs

        except Exception as e:
            print(f"[RAG] Error retrieving meals for user {user_id}: {e}")
            return []

    def bulk_index_user_meals(self, user_id: int, db: Session) -> int:
        """Bulk-index all meals for a user from the database. Returns count."""
        try:
            from app.models.db_models import Meal

            meals = (
                db.query(Meal)
                .filter(Meal.user_id == user_id)
                .order_by(Meal.upload_time.desc())
                .limit(100)
                .all()
            )

            count = 0
            for meal in meals:
                meal_data = {
                    "id": meal.id,
                    "meal_type": meal.meal_type,
                    "upload_date": meal.upload_date.isoformat() if meal.upload_date else "",
                    "analysis_data": meal.analysis_data or {},
                    "nutrition_summary": meal.nutrition_summary or {},
                }
                self.index_user_meal(user_id, meal_data)
                count += 1

            print(f"[RAG] Bulk-indexed {count} meals for user {user_id}")
            return count

        except Exception as e:
            print(f"[RAG] Error bulk-indexing meals for user {user_id}: {e}")
            return 0

    # ------------------------------------------------------------------
    # 3. Conversation memory
    # ------------------------------------------------------------------

    def index_conversation(
        self, user_id: int, session_id: str, role: str, content: str
    ) -> None:
        """Index a conversation turn into the vector store."""
        if self._convo_col is None:
            self._ensure_collections()

        try:
            doc_id = f"convo_{user_id}_{session_id}_{datetime.now().timestamp()}"
            text = f"[{role}] {content}"

            embedding = self._embeddings.embed_query(text)

            self._convo_col.upsert(
                ids=[doc_id],
                documents=[text],
                embeddings=[embedding],
                metadatas=[
                    {
                        "user_id": str(user_id),
                        "session_id": session_id,
                        "role": role,
                        "timestamp": datetime.now().isoformat(),
                    }
                ],
            )
        except Exception as e:
            print(f"[RAG] Error indexing conversation: {e}")

    def retrieve_conversation_context(
        self, user_id: int, query: str, top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant past conversation turns for a user."""
        if self._convo_col is None or self._convo_col.count() == 0:
            return []

        try:
            query_embedding = self._embeddings.embed_query(query)
            results = self._convo_col.query(
                query_embeddings=[query_embedding],
                n_results=min(top_k, self._convo_col.count()),
                where={"user_id": str(user_id)},
                include=["documents", "metadatas", "distances"],
            )

            docs = []
            for idx in range(len(results["ids"][0])):
                docs.append(
                    {
                        "id": results["ids"][0][idx],
                        "content": results["documents"][0][idx],
                        "metadata": results["metadatas"][0][idx],
                        "relevance_score": 1 - results["distances"][0][idx],
                    }
                )
            return docs

        except Exception as e:
            print(f"[RAG] Error retrieving conversation context: {e}")
            return []

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def get_stats(self) -> Dict[str, Any]:
        """Return collection statistics."""
        return {
            "nutrition_knowledge_count": (
                self._nutrition_col.count() if self._nutrition_col else 0
            ),
            "user_meals_count": self._meal_col.count() if self._meal_col else 0,
            "conversation_memory_count": (
                self._convo_col.count() if self._convo_col else 0
            ),
            "chroma_dir": self._chroma_dir,
        }


# Module-level singleton accessor
def get_rag_service() -> RAGService:
    """Get or create the singleton RAG service instance."""
    return RAGService()
