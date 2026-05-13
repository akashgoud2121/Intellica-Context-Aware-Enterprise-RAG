import os
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.config import settings
from app.storage.db import DocumentMetadata
from app.storage.vector_store import vector_store

class DataIngestionPipeline:
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_text(self, text: str) -> List[str]:
        words = text.split()
        chunks = []
        for i in range(0, len(words), self.chunk_size - self.chunk_overlap):
            chunk = " ".join(words[i:i + self.chunk_size])
            chunks.append(chunk)
            if i + self.chunk_size >= len(words):
                break
        return chunks

    def process_and_index(self, filename: str, raw_text: str, data_silo: str, doc_type: str, uploader: str, db: Session):
        """Preprocesses text, chunks it, stores metadata, and indexes into FAISS/BM25."""
        # Save raw document backup
        save_path = os.path.join(settings.STORAGE_DIR, "documents", filename)
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(raw_text)
        
        # Summary generation
        summary = raw_text[:200] + "..." if len(raw_text) > 200 else raw_text
        
        # Store metadata
        doc_meta = DocumentMetadata(
            filename=filename,
            data_silo=data_silo,
            doc_type=doc_type,
            uploaded_by=uploader,
            summary=summary,
            file_path=save_path,
            is_encrypted=True
        )
        db.add(doc_meta)
        db.commit()
        db.refresh(doc_meta)
        
        # Chunking & Embedding
        text_chunks = self.chunk_text(raw_text)
        vector_chunks = []
        for i, chunk in enumerate(text_chunks):
            vector_chunks.append({
                "chunk_id": f"{doc_meta.id}_{i}",
                "doc_id": doc_meta.id,
                "filename": filename,
                "data_silo": data_silo,
                "text": chunk
            })
        
        # Add to vector store
        vector_store.add_documents(vector_chunks)
        return doc_meta

pipeline = DataIngestionPipeline()
