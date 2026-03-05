from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Literal, Optional, List

from app.store.memory import store
from app.store.errors import DocumentNotFoundError, VersionConflictError
from app.domain.changes import (
    apply_replace_changes,
    ChangeValidationError,
    TargetNotFoundError,
)
from app.domain.search import iter_matches


router = APIRouter(prefix="/documents", tags=["documents"])


# ----------------------------
# Pydantic request/response models
# ----------------------------

class CreateDocumentRequest(BaseModel):
    title: Optional[str] = Field(default=None, max_length=200)
    text: str = Field(min_length=0)


class CreateDocumentResponse(BaseModel):
    id: str
    version: int


class DocumentResponse(BaseModel):
    id: str
    title: Optional[str]
    text: str
    version: int


class ReplaceTarget(BaseModel):
    text: str = Field(min_length=1, description="Text to find")
    occurrence: int = Field(ge=1, description="1-based occurrence count")


class ReplaceChange(BaseModel):
    operation: Literal["replace"] = "replace"
    target: ReplaceTarget
    replacement: str = Field(description="Replacement text (can be empty)")


class PatchDocumentRequest(BaseModel):
    baseVersion: Optional[int] = Field(default=None, ge=1, description="Optional optimistic concurrency control")
    changes: List[ReplaceChange] = Field(min_length=1)


class AppliedChange(BaseModel):
    operation: Literal["replace"] = "replace"
    target: ReplaceTarget
    replacement: str
    found_start: int
    found_end: int


class PatchDocumentResponse(BaseModel):
    id: str
    version: int
    text: str
    applied: List[AppliedChange]


class SearchMatch(BaseModel):
    start: int
    end: int
    snippet: str


class SearchResult(BaseModel):
    docId: str
    matches: List[SearchMatch]


class SearchResponse(BaseModel):
    q: str
    results: List[SearchResult]
    limit: int
    offset: int
    returnedMatches: int
    hasMore: bool


# ----------------------------
# Endpoints
# ----------------------------

@router.post("", response_model=CreateDocumentResponse)
def create_document(payload: CreateDocumentRequest):
    doc = store.create(title=payload.title, text=payload.text)
    return CreateDocumentResponse(id=doc.id, version=doc.version)


# IMPORTANT: declare /search BEFORE /{doc_id} to avoid route shadowing
@router.get("/search", response_model=SearchResponse)
def search_documents(
    q: str = Query(min_length=1),
    limit: int = Query(default=10, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    context: int = Query(default=30, ge=0, le=500),
    case_sensitive: bool = Query(default=False),
    doc_id: Optional[List[str]] = Query(default=None, description="Repeatable filter: ?doc_id=a&doc_id=b"),
):
    docs = store.list()
    if doc_id:
        wanted = set(doc_id)
        docs = [d for d in docs if d.id in wanted]

    # Memory-friendly global pagination: stream matches and only keep the ones we return.
    results: List[SearchResult] = []
    global_skipped = 0
    returned = 0
    has_more = False

    for d in docs:
        doc_matches: List[SearchMatch] = []
        for m in iter_matches(d.text, q, context=context, case_sensitive=case_sensitive):
            if global_skipped < offset:
                global_skipped += 1
                continue

            if returned >= limit:
                has_more = True
                break

            doc_matches.append(SearchMatch(start=m["start"], end=m["end"], snippet=m["snippet"]))
            returned += 1

        if doc_matches:
            results.append(SearchResult(docId=d.id, matches=doc_matches))

        if has_more:
            break

    return SearchResponse(
        q=q,
        results=results,
        limit=limit,
        offset=offset,
        returnedMatches=returned,
        hasMore=has_more,
    )


@router.get("/{doc_id}", response_model=DocumentResponse)
def get_document(doc_id: str):
    try:
        doc = store.get(doc_id)
    except DocumentNotFoundError:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentResponse(id=doc.id, title=doc.title, text=doc.text, version=doc.version)


@router.patch("/{doc_id}", response_model=PatchDocumentResponse)
def patch_document(doc_id: str, payload: PatchDocumentRequest):
    try:
        doc = store.get(doc_id)
    except DocumentNotFoundError:
        raise HTTPException(status_code=404, detail="Document not found")

    if payload.baseVersion is not None and payload.baseVersion != doc.version:
        raise HTTPException(status_code=409, detail="Version conflict")

    change_dicts = [
        {
            "target_text": ch.target.text,
            "occurrence": ch.target.occurrence,
            "replacement": ch.replacement,
        }
        for ch in payload.changes
    ]

    try:
        new_text, applied = apply_replace_changes(doc.text, change_dicts)
    except ChangeValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except TargetNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        updated = store.update_text(doc_id=doc_id, new_text=new_text, base_version=payload.baseVersion)
    except DocumentNotFoundError:
        raise HTTPException(status_code=404, detail="Document not found")
    except VersionConflictError:
        raise HTTPException(status_code=409, detail="Version conflict")

    applied_models = [
        AppliedChange(
            target=ReplaceTarget(text=a["target_text"], occurrence=a["occurrence"]),
            replacement=a["replacement"],
            found_start=a["found_start"],
            found_end=a["found_end"],
        )
        for a in applied
    ]

    return PatchDocumentResponse(id=updated.id, version=updated.version, text=updated.text, applied=applied_models)
