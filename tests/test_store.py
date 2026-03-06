import pytest

from app.store.memory import InMemoryDocumentStore
from app.store.errors import DocumentNotFoundError, VersionConflictError


def test_store_get_missing_raises():
    s = InMemoryDocumentStore()
    with pytest.raises(DocumentNotFoundError):
        s.get("doc_missing")


def test_store_update_missing_raises():
    s = InMemoryDocumentStore()
    with pytest.raises(DocumentNotFoundError):
        s.update_text("doc_missing", new_text="x", base_version=1)


def test_store_update_version_conflict_raises():
    s = InMemoryDocumentStore()
    doc = s.create(title="t", text="hello")
    _ = s.update_text(doc.id, new_text="hello2", base_version=1)
    with pytest.raises(VersionConflictError):
        s.update_text(doc.id, new_text="hello3", base_version=1)
