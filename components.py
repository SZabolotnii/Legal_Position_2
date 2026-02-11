from typing import Dict, Any, Optional
from pathlib import Path
from llama_index.core import Settings
from llama_index.core.storage.docstore import SimpleDocumentStore
from llama_index.retrievers.bm25 import BM25Retriever
from llama_index.core.retrievers import QueryFusionRetriever


class SearchComponents:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SearchComponents, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._components = {}
            self._initialized = True

    def initialize_components(self, local_dir: Path) -> bool:
        """Initialize all search components."""
        try:
            # Initialize BM25 Retriever
            print(f"Loading docstore from {local_dir / 'docstore_es_filter.json'}")
            docstore = SimpleDocumentStore.from_persist_path(
                str(local_dir / "docstore_es_filter.json")
            )
            print("Docstore loaded successfully")

            print(f"Loading BM25 retriever from {local_dir / 'bm25_retriever'}")
            bm25_retriever = BM25Retriever.from_persist_dir(
                # str(local_dir / "bm25_retriever_es")
                str(local_dir / "bm25_retriever")
            )
            print("BM25 retriever loaded successfully")

            print(f"Loading BM25 retriever (short) from {local_dir / 'bm25_retriever_short'}")
            bm25_retriever_short = BM25Retriever.from_persist_dir(
                # str(local_dir / "bm25_retriever_es")
                str(local_dir / "bm25_retriever_short")
            )
            print("BM25 retriever (short) loaded successfully")

            # Для коротких текстів створюємо гібридний retriever
            print("Creating QueryFusionRetriever...")
            fusion_retriever = QueryFusionRetriever(
                # [bm25_retriever],
                [bm25_retriever_short],
                similarity_top_k=Settings.similarity_top_k * 2,  # Збільшуємо к-сть результатів перед дедуплікацією
                num_queries=1,
                use_async=True
            )
            print("QueryFusionRetriever created successfully")

            # Store components
            self._components['docstore'] = docstore
            self._components['bm25_retriever'] = bm25_retriever
            self._components['fusion_retriever'] = fusion_retriever

            return True
        except Exception as e:
            print(f"Error initializing components: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    def get_component(self, name: str) -> Optional[Any]:
        """Get a component by name."""
        return self._components.get(name)

    def get_retriever(self) -> Optional[QueryFusionRetriever]:
        """Get the main retriever component."""
        return self.get_component('fusion_retriever')

# Global instance
search_components = SearchComponents()