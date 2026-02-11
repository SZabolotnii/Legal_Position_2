"""
Custom Gemini embedding class for LlamaIndex integration.
Provides an alternative to OpenAI embeddings using Google's Gemini API.
"""
from typing import List
from llama_index.core.embeddings import BaseEmbedding
from google import genai


class GeminiEmbedding(BaseEmbedding):
    """
    Gemini embedding model integration for LlamaIndex.

    Uses Google's gemini-embedding-001 model for generating embeddings.
    This provides an alternative to OpenAI embeddings.
    """

    def __init__(
        self,
        api_key: str,
        model_name: str = "gemini-embedding-001",
        **kwargs
    ):
        """
        Initialize Gemini embedding model.

        Args:
            api_key: Google API key for Gemini
            model_name: Model name (default: gemini-embedding-001)
            **kwargs: Additional arguments for BaseEmbedding
        """
        super().__init__(**kwargs)
        # Use private attribute to store client (Pydantic compatibility)
        self._client = genai.Client(api_key=api_key)
        self._model_name = model_name

    def _get_query_embedding(self, query: str) -> List[float]:
        """
        Get embedding for a query string.

        Args:
            query: Query text to embed

        Returns:
            List of floats representing the embedding vector
        """
        try:
            result = self._client.models.embed_content(
                model=self._model_name,
                contents=query
            )
            # Extract embedding values from the response
            # The response structure is: result.embeddings[0].values
            if hasattr(result, 'embeddings') and len(result.embeddings) > 0:
                embedding = result.embeddings[0]
                if hasattr(embedding, 'values'):
                    return list(embedding.values)

            raise ValueError("Unexpected response structure from Gemini embedding API")

        except Exception as e:
            raise RuntimeError(f"Error getting query embedding from Gemini: {str(e)}")

    def _get_text_embedding(self, text: str) -> List[float]:
        """
        Get embedding for a text string.

        Args:
            text: Text to embed

        Returns:
            List of floats representing the embedding vector
        """
        try:
            result = self._client.models.embed_content(
                model=self._model_name,
                contents=text
            )
            # Extract embedding values from the response
            if hasattr(result, 'embeddings') and len(result.embeddings) > 0:
                embedding = result.embeddings[0]
                if hasattr(embedding, 'values'):
                    return list(embedding.values)

            raise ValueError("Unexpected response structure from Gemini embedding API")

        except Exception as e:
            raise RuntimeError(f"Error getting text embedding from Gemini: {str(e)}")

    async def _aget_query_embedding(self, query: str) -> List[float]:
        """
        Async version of _get_query_embedding.

        Note: Currently uses synchronous API as Gemini SDK doesn't have async support yet.

        Args:
            query: Query text to embed

        Returns:
            List of floats representing the embedding vector
        """
        return self._get_query_embedding(query)

    async def _aget_text_embedding(self, text: str) -> List[float]:
        """
        Async version of _get_text_embedding.

        Note: Currently uses synchronous API as Gemini SDK doesn't have async support yet.

        Args:
            text: Text to embed

        Returns:
            List of floats representing the embedding vector
        """
        return self._get_text_embedding(text)

    def _get_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Get embeddings for a list of texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        embeddings = []
        for text in texts:
            embeddings.append(self._get_text_embedding(text))
        return embeddings
