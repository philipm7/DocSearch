from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_search_doc_id_filter_includes_only_requested_docs():
    r1 = client.post("/documents", json={"title": "a", "text": "foo here"})
    r2 = client.post("/documents", json={"title": "b", "text": "foo there"})
    doc1 = r1.json()["id"]
    doc2 = r2.json()["id"]

    r = client.get("/documents/search", params={"q": "foo", "doc_id": [doc1]})
    assert r.status_code == 200, r.text
    body = r.json()
    assert {res["docId"] for res in body["results"]} == {doc1}
    assert doc2 not in {res["docId"] for res in body["results"]}


def test_search_pagination_sets_has_more_and_stops_after_limit():
    doc1 = client.post("/documents", json={"title": "x", "text": "foo foo foo"}).json()["id"]
    doc2 = client.post("/documents", json={"title": "y", "text": "foo in second doc"}).json()["id"]

    r = client.get("/documents/search", params={"q": "foo", "limit": 1, "offset": 0})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["returnedMatches"] == 1
    assert body["hasMore"] is True
    assert {res["docId"] for res in body["results"]} == {doc1}
    assert doc2 not in {res["docId"] for res in body["results"]}


def test_search_offset_skips_matches_globally():
    doc1 = client.post("/documents", json={"title": "x", "text": "foo foo"}).json()["id"]

    r = client.get("/documents/search", params={"q": "foo", "limit": 10, "offset": 1})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["returnedMatches"] == 1
    assert body["hasMore"] is False
    assert {res["docId"] for res in body["results"]} == {doc1}
    assert body["results"][0]["matches"][0]["start"] == 4


def test_get_document_missing_returns_404_error_shape():
    r = client.get("/documents/doc_missing")
    assert r.status_code == 404
    assert r.json() == {"error": "Document not found", "code": 404}


def test_patch_document_missing_returns_404_error_shape():
    r = client.patch(
        "/documents/doc_missing",
        json={"baseVersion": 1, "changes": [{"operation": "replace", "target": {"text": "a", "occurrence": 1}, "replacement": "b"}]},
    )
    assert r.status_code == 404
    assert r.json() == {"error": "Document not found", "code": 404}


def test_patch_document_target_not_found_returns_400():
    doc_id = client.post("/documents", json={"title": "x", "text": "hello"}).json()["id"]
    r = client.patch(
        f"/documents/{doc_id}",
        json={
            "baseVersion": 1,
            "changes": [{"operation": "replace", "target": {"text": "hello", "occurrence": 2}, "replacement": "hi"}],
        },
    )
    assert r.status_code == 400
    assert r.json()["code"] == 400


def test_patch_document_maps_change_validation_error_to_400(monkeypatch):
    from app.api import documents as documents_api
    from app.domain.changes import ChangeValidationError

    doc_id = client.post("/documents", json={"title": "x", "text": "hello"}).json()["id"]

    def _boom(_text, _changes):
        raise ChangeValidationError("bad change request")

    monkeypatch.setattr(documents_api, "apply_replace_changes", _boom)

    r = client.patch(
        f"/documents/{doc_id}",
        json={"baseVersion": 1, "changes": [{"operation": "replace", "target": {"text": "hello", "occurrence": 1}, "replacement": "hi"}]},
    )
    assert r.status_code == 400
    assert r.json() == {"error": "bad change request", "code": 400}


def test_patch_document_maps_store_update_exceptions(monkeypatch):
    from app.api import documents as documents_api
    from app.store.errors import DocumentNotFoundError, VersionConflictError

    doc_id = client.post("/documents", json={"title": "x", "text": "hello"}).json()["id"]

    def _missing(*args, **kwargs):
        raise DocumentNotFoundError("x")

    monkeypatch.setattr(documents_api.store, "update_text", _missing)
    r = client.patch(
        f"/documents/{doc_id}",
        json={"baseVersion": 1, "changes": [{"operation": "replace", "target": {"text": "hello", "occurrence": 1}, "replacement": "hi"}]},
    )
    assert r.status_code == 404
    assert r.json()["code"] == 404

    def _conflict(*args, **kwargs):
        raise VersionConflictError()

    monkeypatch.setattr(documents_api.store, "update_text", _conflict)
    r = client.patch(
        f"/documents/{doc_id}",
        json={"baseVersion": 1, "changes": [{"operation": "replace", "target": {"text": "hello", "occurrence": 1}, "replacement": "hi"}]},
    )
    assert r.status_code == 409
    assert r.json()["code"] == 409


def test_validation_errors_return_422_in_expected_shape():
    r = client.post("/documents", json={"title": "missing text"})
    assert r.status_code == 422
    body = r.json()
    assert body["code"] == 422
    assert body["error"] == "Validation error"
    assert isinstance(body.get("details"), list)


def test_unhandled_exceptions_return_500_shape(monkeypatch):
    from app import main as main_module

    def _boom():
        raise RuntimeError("kaboom")

    monkeypatch.setattr(main_module.store, "list", _boom)
    crash_client = TestClient(app, raise_server_exceptions=False)
    r = crash_client.get("/")
    assert r.status_code == 500
    assert r.json() == {"error": "Internal server error", "code": 500}
