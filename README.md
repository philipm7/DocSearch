# Legal Tech - Part I - Document Redlining + Search API

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

Open a simple documents table:
- http://localhost:8000/

Run tests:
```bash
pytest -q
```

Tested on Python 3.13

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

## Error handling

- All errors return a JSON object like `{ "error": "message", "code": 400 }`.
- Validation errors use HTTP `422` and include an optional `details` array for debugging.
- Unhandled server errors return HTTP `500` with `{ "error": "Internal server error", "code": 500 }`.

Examples:

**Missing document (404)**
```json
{ "error": "Document not found", "code": 404 }
```

**Version conflict (409)**
```json
{ "error": "Version conflict", "code": 409 }
```

**Schema validation (422)**
```json
{ "error": "Validation error", "code": 422, "details": [{ "...": "..." }] }
```

## Performance notes

- Replace-by-occurrence uses `str.find` repeatedly (near-linear in document size for small occurrence values).
- Search uses a streaming `find` loop and supports `limit/offset` to avoid building huge match lists on large documents.
- Large-doc tests exist to ensure logic works on ~10MB inputs.

## API design rationale

- **Document model:** Each document is stored as plain text with an `id` and monotonically increasing `version`.
- **Editing ("redlining") via PATCH:** Edits are submitted as structured JSON change requests to `PATCH /documents/{id}`.
  - I chose **find/replace by nth occurrence** (`target.text` + `target.occurrence`) because it matches the prompt’s example and supports repeated phrases without ambiguity.
  - Changes are applied **sequentially** to the current document text to keep semantics simple and predictable.
- **Concurrency control:** `baseVersion` provides optimistic concurrency. If it doesn’t match the current version, the API returns `409` to prevent lost updates.
- **Search response shape:** Search returns `start/end` offsets plus a short `snippet` so clients can highlight results in context.
  - Search uses a streaming scan to avoid building large in-memory match lists for large documents.
- **Error format:** All errors return `{ "error": "...", "code": <http_status> }` to keep client handling consistent.

## Example curl

```bash
BASE="http://localhost:8000"

# 1) Create a document
curl -s -X POST "$BASE/documents" \
  -H "Content-Type: application/json" \
  -d '{"title":"NDA","text":"This Agreement is binding. This Agreement is final."}'

# Copy the returned id into DOC_ID
DOC_ID="doc_..."

# 2) Get the document
curl -s "$BASE/documents/$DOC_ID"

# 3) Replace the 2nd occurrence of "Agreement" with "Contract"
curl -s -X PATCH "$BASE/documents/$DOC_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "baseVersion": 1,
    "changes": [
      {
        "operation": "replace",
        "target": { "text": "Agreement", "occurrence": 2 },
        "replacement": "Contract"
      }
    ]
  }'

# 4) Search across all documents
curl -s "$BASE/documents/search?q=Contract&limit=10&offset=0&context=30"
```
