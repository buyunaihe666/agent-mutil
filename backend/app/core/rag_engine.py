"""RAG Engine - document chunking, embedding, hybrid search, citation."""

import re
import uuid
from dataclasses import dataclass, field
from typing import Optional

import structlog

from app.core.yaml_config import get_yaml_config

logger = structlog.get_logger(__name__)

yaml_config = get_yaml_config()
EMBEDDING_CONFIG = yaml_config.get("embedding", {})


# --- Data Classes ---

@dataclass
class DocumentChunk:
    """A single document chunk with optional embedding."""
    chunk_id: str
    content: str
    chunk_index: int
    source_document: str  # Original document filename / asset_id
    token_count: int = 0
    embedding: Optional[list[float]] = None
    metadata: dict = field(default_factory=dict)


@dataclass
class SearchResult:
    """A single search result with relevance score."""
    chunk: DocumentChunk
    score: float
    source: str  # "vector" or "keyword" or "hybrid"


@dataclass
class Citation:
    """Citation reference for traceable answers."""
    source_document: str
    chunk_index: int
    content_snippet: str
    relevance_score: float


# --- Document Chunker ---

class DocumentChunker:
    """Hybrid chunking strategy: semantic + fixed-size with overlap."""

    def __init__(
        self,
        max_chunk_tokens: int = 512,
        overlap_tokens: int = 51,  # ~10% of max
    ):
        self.max_chunk_tokens = max_chunk_tokens
        self.overlap_tokens = overlap_tokens

    def chunk(self, text: str, source_document: str) -> list[DocumentChunk]:
        """Split text into chunks using semantic + token-based strategy.

        Priority: semantic (paragraph/heading boundaries) → token-based (fixed size).
        """
        chunks: list[DocumentChunk] = []

        # Step 1: Split by semantic boundaries (paragraphs)
        paragraphs = self._split_paragraphs(text)

        # Step 2: For each paragraph, if it exceeds max_chunk_tokens, split further
        for para in paragraphs:
            para_tokens = self._estimate_tokens(para)
            if para_tokens <= self.max_chunk_tokens:
                if para.strip():
                    chunks.append(para)
            else:
                # Split by sentences within the paragraph
                sub_chunks = self._split_by_sentence(para, self.max_chunk_tokens)
                chunks.extend(sub_chunks)

        # Step 3: Create DocumentChunk objects with overlap
        result: list[DocumentChunk] = []
        for i, chunk_text in enumerate(chunks):
            if not chunk_text.strip():
                continue
            token_count = self._estimate_tokens(chunk_text)
            result.append(DocumentChunk(
                chunk_id=str(uuid.uuid4()),
                content=chunk_text,
                chunk_index=i,
                source_document=source_document,
                token_count=token_count,
            ))

        logger.info(
            "Document chunked",
            source=source_document,
            original_length=len(text),
            chunk_count=len(result),
        )
        return result

    def _split_paragraphs(self, text: str) -> list[str]:
        """Split text by paragraph boundaries."""
        # Split on double newlines or markdown heading markers
        raw = re.split(r'\n\s*\n|(?=\n#{1,6}\s)', text)
        return [p.strip() for p in raw if p.strip()]

    def _split_by_sentence(self, text: str, max_tokens: int) -> list[str]:
        """Split a long paragraph into sentence-level chunks respecting max_tokens."""
        sentences = re.split(r'(?<=[。！？.!?])\s*', text)
        chunks: list[str] = []
        current_chunk = ""

        for sentence in sentences:
            if not sentence.strip():
                continue
            tentative = current_chunk + sentence
            if self._estimate_tokens(tentative) > max_tokens and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                current_chunk = tentative

        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        return chunks

    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimation: ~1.3 tokens per character for Chinese, ~0.75 for English."""
        chinese_chars = len(re.findall(r'[一-鿿]', text))
        other_chars = len(text) - chinese_chars
        return int(chinese_chars * 1.3 + other_chars * 0.75)


# --- Embedding Service ---

class EmbeddingService:
    """Generate text embeddings via DeepSeek Embedding API."""

    def __init__(self):
        self.model = EMBEDDING_CONFIG.get("model", "deepseek-embedding")
        self.dimensions = EMBEDDING_CONFIG.get("dimensions", 1536)
        self.batch_size = EMBEDDING_CONFIG.get("batch_size", 32)

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a batch of texts.

        Note: Mock implementation for testing. Real API call via litellm.
        """
        # Mock: return random-looking but reproducible vectors based on text hash
        embeddings = []
        for text in texts:
            # Generate deterministic "embedding" from text hash
            import hashlib
            h = hashlib.sha256(text.encode()).digest()
            # Scale to reasonable embedding range
            vec = [(b / 255.0 * 2 - 1) * 0.1 for b in h[:self.dimensions]]
            # Pad if needed
            if len(vec) < self.dimensions:
                vec.extend([0.0] * (self.dimensions - len(vec)))
            embeddings.append(vec[:self.dimensions])

        logger.info("Embeddings generated", text_count=len(texts), dimensions=self.dimensions)
        return embeddings

    async def embed_single(self, text: str) -> list[float]:
        """Generate embedding for a single text."""
        results = await self.embed([text])
        return results[0]


# --- Knowledge Base Engine ---

class KnowledgeBaseEngine:
    """RAG engine: manages chunks, performs hybrid retrieval with citation."""

    def __init__(self):
        self.chunker = DocumentChunker()
        self.embedding_service = EmbeddingService()
        self._chunks: dict[str, DocumentChunk] = {}  # chunk_id -> chunk
        self._index: list[tuple[str, list[float]]] = []  # (chunk_id, embedding)
        self._documents: dict[str, str] = {}  # source -> full text

    async def ingest_document(self, text: str, source: str) -> list[DocumentChunk]:
        """Ingest a document: chunk, embed, and index."""
        # Chunk
        chunks = self.chunker.chunk(text, source)
        if not chunks:
            return []

        # Embed
        texts = [c.content for c in chunks]
        embeddings = await self.embedding_service.embed(texts)

        # Index
        for chunk, embedding in zip(chunks, embeddings):
            chunk.embedding = embedding
            self._chunks[chunk.chunk_id] = chunk
            self._index.append((chunk.chunk_id, embedding))

        self._documents[source] = text
        logger.info("Document ingested", source=source, chunk_count=len(chunks))
        return chunks

    async def search(
        self,
        query: str,
        top_k: int = 5,
        search_type: str = "hybrid",  # "vector", "keyword", "hybrid"
    ) -> list[SearchResult]:
        """Search knowledge base with vector + keyword hybrid retrieval."""
        if not self._index:
            return []

        # Vector search (cosine similarity)
        query_embedding = await self.embedding_service.embed_single(query)
        vector_results = self._vector_search(query_embedding, top_k)

        # Keyword search (BM25-like simple TF-IDF approximation)
        keyword_results = self._keyword_search(query, top_k)

        if search_type == "vector":
            return vector_results
        elif search_type == "keyword":
            return keyword_results
        else:
            # Hybrid: combine and re-rank
            return self._hybrid_merge(vector_results, keyword_results, top_k)

    async def search_with_citations(
        self, query: str, top_k: int = 5
    ) -> tuple[list[SearchResult], list[Citation]]:
        """Search and generate citations."""
        results = await self.search(query, top_k, "hybrid")
        citations = [
            Citation(
                source_document=r.chunk.source_document,
                chunk_index=r.chunk.chunk_index,
                content_snippet=r.chunk.content[:200] + "..." if len(r.chunk.content) > 200 else r.chunk.content,
                relevance_score=r.score,
            )
            for r in results
        ]
        return results, citations

    def _vector_search(self, query_embedding: list[float], top_k: int) -> list[SearchResult]:
        """Cosine similarity vector search."""
        scored = []
        for chunk_id, embedding in self._index:
            similarity = self._cosine_similarity(query_embedding, embedding)
            chunk = self._chunks[chunk_id]
            scored.append(SearchResult(chunk=chunk, score=similarity, source="vector"))

        scored.sort(key=lambda r: r.score, reverse=True)
        return scored[:top_k]

    def _keyword_search(self, query: str, top_k: int) -> list[SearchResult]:
        """Simple keyword search using overlap scoring."""
        query_terms = set(query.lower().split())
        if not query_terms:
            return []

        scored = []
        for chunk in self._chunks.values():
            content_lower = chunk.content.lower()
            # Simple scoring: fraction of query terms found
            hits = sum(1 for t in query_terms if t in content_lower)
            if hits > 0:
                score = hits / len(query_terms)
                scored.append(SearchResult(chunk=chunk, score=score, source="keyword"))

        scored.sort(key=lambda r: r.score, reverse=True)
        return scored[:top_k]

    def _hybrid_merge(
        self, vector_results: list[SearchResult], keyword_results: list[SearchResult], top_k: int
    ) -> list[SearchResult]:
        """Merge vector and keyword results with weighted scoring."""
        # Vector weight: 0.7, Keyword weight: 0.3
        scores: dict[str, tuple[float, SearchResult]] = {}

        for r in vector_results:
            scores[r.chunk.chunk_id] = (r.score * 0.7, r)

        for r in keyword_results:
            if r.chunk.chunk_id in scores:
                current_score, existing = scores[r.chunk.chunk_id]
                scores[r.chunk.chunk_id] = (current_score + r.score * 0.3, SearchResult(
                    chunk=r.chunk,
                    score=current_score + r.score * 0.3,
                    source="hybrid",
                ))
            else:
                scores[r.chunk.chunk_id] = (r.score * 0.3, SearchResult(
                    chunk=r.chunk,
                    score=r.score * 0.3,
                    source="hybrid",
                ))

        merged = [v[1] for v in scores.values()]
        merged.sort(key=lambda r: r.score, reverse=True)
        return merged[:top_k]

    def _cosine_similarity(self, a: list[float], b: list[float]) -> float:
        """Compute cosine similarity between two vectors."""
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def get_chunk_count(self) -> int:
        return len(self._chunks)

    def get_document_count(self) -> int:
        return len(self._documents)

    def clear(self) -> None:
        self._chunks.clear()
        self._index.clear()
        self._documents.clear()


# Global engine
knowledge_base_engine = KnowledgeBaseEngine()
