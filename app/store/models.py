from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class Document:
    id: str
    title: Optional[str]
    text: str
    version: int
    created_at: datetime
    updated_at: datetime
