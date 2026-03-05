# Legal Tech - Part I (Backend Only) — Document Redlining + Search API

This is a small FastAPI service that:
- Stores text documents
- Applies "redlining" change requests via JSON (find/replace by nth occurrence)
- Searches across document contents and returns snippets

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

uvicorn app.main:app --reload
```

Open interactive docs:
- http://localhost:8000/docs

Run tests:
```bash
pytest -q
```

## API overview

### Create a document
`POST /documents`

Body:
```json
{ "title": "NDA", "text": "This Agreement ..." }
```

### Get a document
`GET /documents/{id}`

### Apply changes (find/replace)
`PATCH /documents/{id}`

Body:
```json
{
  "baseVersion": 1,
  "changes": [
    {
      "operation": "replace",
      "target": { "text": "Agreement", "occurrence": 1 },
      "replacement": "Contract"
    }
  ]
}
```

Notes:
- Changes apply **sequentially** to the current text.
- If `baseVersion` is provided and does not match the current document version, returns `409`.

### Search across documents
`GET /documents/search?q=contract&limit=10&offset=0&context=30`

Optional filters:
- `doc_id=...` (repeatable) to search only specific documents.
- `case_sensitive=true`

Response includes match offsets, a context snippet, and pagination fields (returnedMatches, hasMore).

## Error format

All errors return a JSON object like:
```json
{ "error": "message", "code": 400 }
```

## Performance notes

- Replace-by-occurrence uses `str.find` repeatedly (near-linear in document size for small occurrence values).
- Search uses a streaming `find` loop and supports `limit/offset` to avoid building huge match lists on large documents.
- Large-doc tests exist to ensure logic works on ~10MB inputs.
