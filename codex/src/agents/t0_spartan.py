"""T0 Spartan agent for initial scroll validation."""
from models.scroll import Scroll, RoutingHeader, Provenance
from typing import Dict, Any
import uuid

REQUIRED_FIELDS = ["source", "content", "facts"]


def validate_raw(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Validate raw payload against required fields."""
    diag = {"schema_ok": True, "missing": [], "facts_ok": True}
    for k in REQUIRED_FIELDS:
        if k not in payload:
            diag["schema_ok"] = False
            diag["missing"].append(k)
    facts = payload.get("facts", [])
    diag["facts_ok"] = isinstance(facts, list)
    return diag


def create_t0_scroll(raw: Dict[str, Any], correlation_id: str) -> Scroll:
    """Create a T0 validated scroll from raw payload."""
    diag = validate_raw(raw)
    content_hash = Scroll.hash_payload(raw)
    header = RoutingHeader(
        tier="T0",
        kind="VALIDATED" if diag["schema_ok"] and diag["facts_ok"] else "INIT",
        correlation_id=correlation_id
    )
    prov = Provenance(
        source=str(raw.get("source", "unknown")),
        actor="T0_SPARTAN_CORE",
        content_hash=content_hash
    )
    return Scroll(
        id=str(uuid.uuid4()),
        header=header,
        payload=raw,
        provenance=prov,
        diagnostics=diag
    )


def t0_spartan_node(state):
    """T0 Spartan node for LangGraph."""
    logs = state.get("logs", [])
    inbox = state.get("inbox", [])
    if not inbox:
        logs.append("[T0] nothing to process")
        state["logs"] = logs
        return state

    current = inbox.pop(0)
    # T0 expects raw payload under current.payload["raw"]
    raw = current.payload.get("raw", current.payload)
    t0_out = create_t0_scroll(raw, current.header.correlation_id)

    # Decide promotion: if valid -> route T1 else keep at T0
    if t0_out.diagnostics.get("schema_ok") and t0_out.diagnostics.get("facts_ok"):
        t0_out.header.route_to = "T1"
        state["route"] = "T1"
        logs.append("[T0] validated; routing to T1")
    else:
        t0_out.header.route_to = "T0"
        state["route"] = "T0"
        logs.append(f"[T0] validation failed; missing={t0_out.diagnostics.get('missing')}")

    # Ledger and outbox
    ledger = state.get("ledger", [])
    ledger.append(t0_out)
    state["ledger"] = ledger
    state["logs"] = logs
    state["inbox"] = inbox
    return state
