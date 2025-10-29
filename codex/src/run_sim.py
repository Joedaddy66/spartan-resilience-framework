"""Demo simulation runner."""
from models.scroll import Scroll, RoutingHeader, Provenance
from core.state import init_state
from graph.simulation import build_graph


def seed_scroll():
    """Create a seed scroll for testing."""
    raw = {
        "source": "ingest.form:v1",
        "content": {"title": "Example", "body": "Hello, Codex."},
        "facts": ["alpha", "beta"]
    }
    initial = Scroll(
        id="seed-0001",
        header=RoutingHeader(tier="T0", kind="INIT", correlation_id="corr-seed-1"),
        payload={"raw": raw},
        provenance=Provenance(source="seed", actor="system", content_hash=Scroll.hash_payload(raw))
    )
    return initial


if __name__ == "__main__":
    graph = build_graph()
    state = init_state(seed_scroll())

    # Execute a few steps to show flow
    for _ in range(4):
        state = graph.invoke(state)

    print("\n--- LOGS ---")
    for line in state.get("logs", []):
        print(line)

    print("\n--- LEDGER (last) ---")
    led = state.get("ledger", [])
    if led:
        last = led[-1]
        print("id:", last.id, "tier:", last.header.tier, "route_to:", last.header.route_to)
        print("diagnostics:", last.diagnostics)
