"""Scroll data models."""
from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Literal, Dict, Any, List, Optional
import hashlib
import json
import time

Tier = Literal["T0", "T1", "T2", "END"]


class RoutingHeader(BaseModel):
    """Routing header for scroll metadata."""
    tier: Tier
    kind: str  # e.g., "INIT", "VALIDATED", "DISPATCH"
    route_to: Optional[Tier] = None
    created_at: float = Field(default_factory=lambda: time.time())
    correlation_id: str


class Provenance(BaseModel):
    """Provenance information for scroll."""
    source: str
    actor: str
    signatures: List[str] = []  # placeholder for future crypto
    content_hash: str


class Scroll(BaseModel):
    """Main scroll data structure."""
    id: str
    header: RoutingHeader
    payload: Dict[str, Any]
    provenance: Provenance
    diagnostics: Dict[str, Any] = {}

    @staticmethod
    def hash_payload(payload: Dict[str, Any]) -> str:
        """Generate SHA-256 hash of payload."""
        blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(blob).hexdigest()
