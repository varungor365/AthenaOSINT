"""
Intelligence Store using LlamaIndex.
Indexes uploaded documents for RAG (Retrieval-Augmented Generation).
"""

from pathlib import Path
from loguru import logger
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext, load_index_from_storage

# Storage Path for Vector Index
INDEX_DIR = Path("data/vector_store")

class IntelligenceStore:
    def __init__(self):
        self.index = None
        self._load_or_create_index()

    def _load_or_create_index(self):
        """Load existing index or create new one."""
        try:
            if not INDEX_DIR.exists():
                INDEX_DIR.mkdir(parents=True, exist_ok=True)
                self.index = VectorStoreIndex([]) # Empty index
                self.index.storage_context.persist(persist_dir=str(INDEX_DIR))
            else:
                storage_context = StorageContext.from_defaults(persist_dir=str(INDEX_DIR))
                self.index = load_index_from_storage(storage_context)
                logger.info("Loaded Intelligence Store from disk.")
        except Exception as e:
            logger.error(f"Failed to load Intelligence Store: {e}")
            self.index = VectorStoreIndex([])

    def ingest_document(self, file_path: str):
        """Ingest a single document into the index."""
        try:
            documents = SimpleDirectoryReader(input_files=[file_path]).load_data()
            if self.index:
                for doc in documents:
                    self.index.insert(doc)
                
                # Persist
                self.index.storage_context.persist(persist_dir=str(INDEX_DIR))
                logger.info(f"Ingested document: {Path(file_path).name}")
                return True
        except Exception as e:
            logger.error(f"Ingestion failed: {e}")
            return False

    def query(self, question: str) -> str:
        """Query the knowledge base."""
        if not self.index:
            return "Intelligence Store is not initialized."
        try:
            query_engine = self.index.as_query_engine()
            response = query_engine.query(question)
            return str(response)
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return "I simply cannot recall that information right now."
