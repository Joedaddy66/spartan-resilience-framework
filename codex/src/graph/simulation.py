"""LangGraph simulation for scroll flow."""
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from core.state import CodexState
from shells.facilitator import facilitator_node
from shells.orchestrator import orchestrator_node
from agents.t0_spartan import t0_spartan_node


def build_graph():
    """Build and compile the LangGraph workflow."""
    graph = StateGraph(CodexState)

    graph.add_node("Facilitator", facilitator_node)
    graph.add_node("Orchestrator", orchestrator_node)
    graph.add_node("T0_Spartan", t0_spartan_node)

    graph.set_entry_point("Facilitator")

    # Facilitator always hands to Orchestrator
    graph.add_edge("Facilitator", "Orchestrator")

    # Orchestrator chooses next hop based on state["route"]
    def route_selector(state: Dict[str, Any]) -> str:
        route = state.get("route", "T0")
        return {
            "T0": "T0_Spartan",
            "T1": END,  # stub: plug a T1 node later
            "END": END
        }.get(route, "T0_Spartan")

    graph.add_conditional_edges("Orchestrator", route_selector, {
        "T0_Spartan": "T0_Spartan",
        END: END
    })

    # After T0, bounce back to Orchestrator (may promote to T1 or retry T0)
    graph.add_edge("T0_Spartan", "Orchestrator")

    return graph.compile()
