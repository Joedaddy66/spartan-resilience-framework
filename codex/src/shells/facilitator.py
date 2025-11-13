"""Facilitator shell for initial scroll processing."""
from typing import Dict, Any
from models.scroll import Scroll
import time


def facilitator_node(state: Dict[str, Any]):
    """Facilitator node for LangGraph."""
    logs = state.get("logs", [])
    inbox = state.get("inbox", [])
    if not inbox:
        logs.append("[Facilitator] idle")
        state["logs"] = logs
        return state

    s: Scroll = inbox[0]
    logs.append(f"[Facilitator] received scroll {s.id} tier={s.header.tier} kind={s.header.kind}")
    # Basic header sanity; ensure correlation id exists
    if not s.header.correlation_id:
        s.header.correlation_id = f"corr-{int(time.time()*1000)}"
        logs.append("[Facilitator] stamped correlation_id")

    # Set next route hint to current tier (start at T0)
    state["route"] = s.header.tier
    state["logs"] = logs
    return state
