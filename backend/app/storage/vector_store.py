import os
import pickle
import numpy as np
from typing import List, Dict, Any, Tuple
import faiss
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi
from app.config import settings

class EnterpriseVectorStore:
    def __init__(self):
        self.embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
        self.dimension = self.embedding_model.get_sentence_embedding_dimension()
        self.index_path = settings.VECTOR_STORE_PATH + ".index"
        self.meta_path = settings.VECTOR_STORE_PATH + "_meta.pkl"
        
        self.index: faiss.IndexFlatL2 = None
        self.chunks: List[Dict[str, Any]] = []
        self.bm25: BM25Okapi = None
        self.tokenized_corpus: List[List[str]] = []

        self._load_or_create_index()

    def _load_or_create_index(self):
        if os.path.exists(self.index_path) and os.path.exists(self.meta_path):
            try:
                self.index = faiss.read_index(self.index_path)
                with open(self.meta_path, 'rb') as f:
                    self.chunks = pickle.load(f)
                self._rebuild_bm25()
            except Exception as e:
                print(f"Warning: Failed to load existing index: {e}. Reinitializing...")
                self._initialize_empty()
        else:
            self._initialize_empty()

    def _initialize_empty(self):
        self.index = faiss.IndexFlatL2(self.dimension)
        self.chunks = []
        self.bm25 = None
        self.tokenized_corpus = []

    def _rebuild_bm25(self):
        if not self.chunks:
            self.bm25 = None
            self.tokenized_corpus = []
            return
        self.tokenized_corpus = [chunk["text"].lower().split() for chunk in self.chunks]
        self.bm25 = BM25Okapi(self.tokenized_corpus)

    def save_index(self):
        faiss.write_index(self.index, self.index_path)
        with open(self.meta_path, 'wb') as f:
            pickle.dump(self.chunks, f)

    def add_documents(self, chunks: List[Dict[str, Any]]):
        if not chunks:
            return
        texts = [c["text"] for c in chunks]
        embeddings = self.embedding_model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
        
        # Add to FAISS
        self.index.add(embeddings)
        self.chunks.extend(chunks)
        
        # Update BM25
        self._rebuild_bm25()
        self.save_index()

    def semantic_search(self, query: str, top_k: int = 5, silo_filter: str = None) -> List[Tuple[Dict[str, Any], float]]:
        if self.index.ntotal == 0:
            return []
        
        query_vector = self.embedding_model.encode([query], convert_to_numpy=True)
        distances, indices = self.index.search(query_vector, min(top_k * 3, self.index.ntotal)) # fetch extra for filtering
        
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1 or idx >= len(self.chunks):
                continue
            chunk = self.chunks[idx]
            if silo_filter and chunk.get("data_silo") != silo_filter:
                continue
            # Convert L2 distance to similarity score between 0 and 1
            sim_score = max(0.0, 1.0 - (dist / 100.0))
            results.append((chunk, sim_score))
            if len(results) >= top_k:
                break
        return results

    def keyword_search(self, query: str, top_k: int = 5, silo_filter: str = None) -> List[Tuple[Dict[str, Any], float]]:
        if not self.bm25 or not self.chunks:
            return []
        
        tokenized_query = query.lower().split()
        scores = self.bm25.get_scores(tokenized_query)
        
        # Rank indices
        top_indices = np.argsort(scores)[::-1]
        
        results = []
        for idx in top_indices:
            score = float(scores[idx])
            if score <= 0:
                continue
            chunk = self.chunks[idx]
            if silo_filter and chunk.get("data_silo") != silo_filter:
                continue
            # Normalize score roughly
            norm_score = min(1.0, score / 10.0)
            results.append((chunk, norm_score))
            if len(results) >= top_k:
                break
        return results

vector_store = EnterpriseVectorStore()
