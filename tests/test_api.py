from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_create_get_patch_search_happy_path():
    # Create
    r = client.post("/documents", json={"title": "NDA", "text": "This Agreement is binding. Agreement."})
    assert r.status_code == 200, r.text
    doc_id = r.json()["id"]

    # Get
    r = client.get(f"/documents/{doc_id}")
    assert r.status_code == 200
    assert r.json()["version"] == 1

    # Patch (replace 1st occurrence)
    r = client.patch(
        f"/documents/{doc_id}",
        json={
            "baseVersion": 1,
            "changes": [
                {
                    "operation": "replace",
                    "target": {"text": "Agreement", "occurrence": 1},
                    "replacement": "Contract",
                }
            ],
        },
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["version"] == 2
    assert body["text"].startswith("This Contract")

    # Search
    r = client.get("/documents/search", params={"q": "Contract", "limit": 10, "offset": 0})
    assert r.status_code == 200, r.text
    sr = r.json()
    assert sr["returnedMatches"] >= 1
    assert any(res["docId"] == doc_id for res in sr["results"])


def test_version_conflict_returns_409():
    r = client.post("/documents", json={"title": "x", "text": "hello hello"})
    doc_id = r.json()["id"]

    r = client.patch(
        f"/documents/{doc_id}",
        json={
            "baseVersion": 999,
            "changes": [
                {"operation": "replace", "target": {"text": "hello", "occurrence": 1}, "replacement": "hi"}
            ],
        },
    )
    assert r.status_code == 409
    assert r.json()["code"] == 409
