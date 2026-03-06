from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_homepage_renders_document_table():
    r = client.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers.get("content-type", "")
    body = r.text
    assert "DocSearch" in body
    assert "<table" in body
    assert "<th>ID</th>" in body
    assert "<th>Title</th>" in body
    assert "API docs" in body

