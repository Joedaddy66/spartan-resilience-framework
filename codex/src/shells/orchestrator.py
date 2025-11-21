"""Orchestrator shell for scroll routing."""
from typing import Dict, Any
from models.scroll import Scroll


def orchestrator_node(state: Dict[str, Any]):
    """Orchestrator node for LangGraph."""
    logs = state.get("logs", [])
    route = state.get("route", "T0")

    # The orchestrator dispatches based on the route state
    if route == "T0":
        logs.append("[Orchestrator] dispatch -> T0_Spartan")
    elif route == "T1":
        logs.append("[Orchestrator] dispatch -> T1_Sentinel (stub)")
    elif route == "END":
        logs.append("[Orchestrator] reached END")
    else:
        logs.append(f"[Orchestrator] unknown route={route}; default T0")

    state["logs"] = logs
    return state
