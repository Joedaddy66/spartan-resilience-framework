"""Core state management for Codex."""
from typing import TypedDict, List
from models.scroll import Scroll


class CodexState(TypedDict, total=False):
    """State structure for LangGraph."""
    inbox: List[Scroll]  # incoming scrolls to be processed
    ledger: List[Scroll]  # append-only processed scrolls
    logs: List[str]  # textual trace
    route: str  # current route hint (e.g., "T0","T1","END")


def init_state(first: Scroll) -> CodexState:
    """Initialize state with first scroll."""
    return {"inbox": [first], "ledger": [], "logs": [], "route": "T0"}
