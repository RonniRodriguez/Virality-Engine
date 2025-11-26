"""
Idea Inc - Vector Store

ChromaDB-based vector store for idea embeddings and agent memory.
Supports semantic search and RAG operations.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from shared.utils.logging import get_logger

logger = get_logger(__name__)

# Try to import ChromaDB
try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False
    logger.warning("ChromaDB not available, vector store will be disabled")


class VectorStore:
    """
    Vector store for idea embeddings and semantic search.
    
    Uses ChromaDB for storage and retrieval.
    Falls back to simple text matching if ChromaDB is not available.
    """
    
    def __init__(
        self,
        persist_directory: str = "./data/chroma",
        collection_name: str = "ideas",
    ):
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.client = None
        self.collection = None
        self.enabled = CHROMA_AVAILABLE
        
        # Fallback in-memory storage
        self._fallback_store: Dict[str, Dict[str, Any]] = {}
    
    async def initialize(self) -> None:
        """Initialize the vector store"""
        if not self.enabled:
            logger.info("Vector store disabled (ChromaDB not available)")
            return
        
        try:
            # Create persist directory
            Path(self.persist_directory).mkdir(parents=True, exist_ok=True)
            
            # Initialize ChromaDB client
            self.client = chromadb.Client(ChromaSettings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=self.persist_directory,
                anonymized_telemetry=False,
            ))
            
            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            
            logger.info(
                "Vector store initialized",
                collection=self.collection_name,
                count=self.collection.count(),
            )
            
        except Exception as e:
            logger.error("Failed to initialize vector store", error=str(e))
            self.enabled = False
    
    async def add_idea(
        self,
        idea_id: UUID,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Add an idea to the vector store.
        
        Args:
            idea_id: Unique idea identifier
            text: Idea text content
            metadata: Optional metadata (tags, creator, etc.)
        
        Returns:
            Embedding ID
        """
        embedding_id = str(idea_id)
        
        if self.enabled and self.collection:
            try:
                self.collection.add(
                    ids=[embedding_id],
                    documents=[text],
                    metadatas=[metadata or {}],
                )
                logger.debug("Added idea to vector store", idea_id=embedding_id)
            except Exception as e:
                logger.error("Failed to add idea to vector store", error=str(e))
                # Fall back to in-memory
                self._fallback_store[embedding_id] = {
                    "text": text,
                    "metadata": metadata or {},
                }
        else:
            # Fallback storage
            self._fallback_store[embedding_id] = {
                "text": text,
                "metadata": metadata or {},
            }
        
        return embedding_id
    
    async def search_similar(
        self,
        query: str,
        n_results: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for similar ideas.
        
        Args:
            query: Query text
            n_results: Number of results to return
            filter_metadata: Optional metadata filter
        
        Returns:
            List of similar ideas with scores
        """
        if self.enabled and self.collection:
            try:
                results = self.collection.query(
                    query_texts=[query],
                    n_results=n_results,
                    where=filter_metadata,
                )
                
                # Format results
                similar = []
                if results["ids"] and results["ids"][0]:
                    for i, idea_id in enumerate(results["ids"][0]):
                        similar.append({
                            "idea_id": idea_id,
                            "text": results["documents"][0][i] if results["documents"] else "",
                            "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                            "distance": results["distances"][0][i] if results["distances"] else 0,
                        })
                
                return similar
                
            except Exception as e:
                logger.error("Vector search failed", error=str(e))
                return self._fallback_search(query, n_results)
        else:
            return self._fallback_search(query, n_results)
    
    def _fallback_search(
        self,
        query: str,
        n_results: int = 5,
    ) -> List[Dict[str, Any]]:
        """Simple text-based fallback search"""
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        scored = []
        for idea_id, data in self._fallback_store.items():
            text_lower = data["text"].lower()
            text_words = set(text_lower.split())
            
            # Simple word overlap score
            overlap = len(query_words & text_words)
            if overlap > 0:
                score = overlap / max(len(query_words), len(text_words))
                scored.append({
                    "idea_id": idea_id,
                    "text": data["text"],
                    "metadata": data["metadata"],
                    "distance": 1 - score,  # Convert to distance
                })
        
        # Sort by distance (ascending)
        scored.sort(key=lambda x: x["distance"])
        return scored[:n_results]
    
    async def get_idea(self, idea_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get an idea by ID.
        
        Args:
            idea_id: Idea identifier
        
        Returns:
            Idea data or None if not found
        """
        embedding_id = str(idea_id)
        
        if self.enabled and self.collection:
            try:
                results = self.collection.get(ids=[embedding_id])
                if results["ids"]:
                    return {
                        "idea_id": results["ids"][0],
                        "text": results["documents"][0] if results["documents"] else "",
                        "metadata": results["metadatas"][0] if results["metadatas"] else {},
                    }
            except Exception as e:
                logger.error("Failed to get idea from vector store", error=str(e))
        
        # Fallback
        if embedding_id in self._fallback_store:
            data = self._fallback_store[embedding_id]
            return {
                "idea_id": embedding_id,
                "text": data["text"],
                "metadata": data["metadata"],
            }
        
        return None
    
    async def delete_idea(self, idea_id: UUID) -> bool:
        """
        Delete an idea from the vector store.
        
        Args:
            idea_id: Idea identifier
        
        Returns:
            True if deleted, False otherwise
        """
        embedding_id = str(idea_id)
        
        if self.enabled and self.collection:
            try:
                self.collection.delete(ids=[embedding_id])
                logger.debug("Deleted idea from vector store", idea_id=embedding_id)
                return True
            except Exception as e:
                logger.error("Failed to delete idea from vector store", error=str(e))
        
        # Fallback
        if embedding_id in self._fallback_store:
            del self._fallback_store[embedding_id]
            return True
        
        return False
    
    async def get_context_for_idea(
        self,
        idea_text: str,
        n_context: int = 3,
    ) -> str:
        """
        Get context for RAG by finding similar ideas.
        
        Args:
            idea_text: Idea to find context for
            n_context: Number of context items
        
        Returns:
            Formatted context string
        """
        similar = await self.search_similar(idea_text, n_results=n_context)
        
        if not similar:
            return "No similar ideas found."
        
        context_parts = ["Similar ideas in the system:"]
        for i, item in enumerate(similar, 1):
            context_parts.append(f"{i}. {item['text'][:200]}")
        
        return "\n".join(context_parts)
    
    @property
    def count(self) -> int:
        """Get total number of stored ideas"""
        if self.enabled and self.collection:
            return self.collection.count()
        return len(self._fallback_store)

