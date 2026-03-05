from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional
from uuid import uuid4
import threading

from app.store.models import Document
from app.store.errors import DocumentNotFoundError, VersionConflictError


class InMemoryDocumentStore:
    """
    Simple in-memory store for prototype usage.

    Thread-safety: protected by an RLock to keep read/modify/write safe.
    """

    def __init__(self):
        self._lock = threading.RLock()
        self._docs: Dict[str, Document] = {}

    def create(self, title: Optional[str], text: str) -> Document:
        with self._lock:
            now = datetime.utcnow()
            doc_id = f"doc_{uuid4().hex}"
            doc = Document(
                id=doc_id,
                title=title,
                text=text,
                version=1,
                created_at=now,
                updated_at=now,
            )
            self._docs[doc_id] = doc
            return doc

    def get(self, doc_id: str) -> Document:
        with self._lock:
            doc = self._docs.get(doc_id)
            if doc is None:
                raise DocumentNotFoundError(doc_id)
            return doc

    def list(self) -> List[Document]:
        with self._lock:
            # stable ordering by created time for predictable tests
            return sorted(self._docs.values(), key=lambda d: d.created_at)

    def update_text(self, doc_id: str, new_text: str, base_version: Optional[int] = None) -> Document:
        with self._lock:
            doc = self._docs.get(doc_id)
            if doc is None:
                raise DocumentNotFoundError(doc_id)

            if base_version is not None and base_version != doc.version:
                raise VersionConflictError()

            now = datetime.utcnow()
            updated = Document(
                id=doc.id,
                title=doc.title,
                text=new_text,
                version=doc.version + 1,
                created_at=doc.created_at,
                updated_at=now,
            )
            self._docs[doc_id] = updated
            return updated


# Module-level singleton store for this prototype.
store = InMemoryDocumentStore()
