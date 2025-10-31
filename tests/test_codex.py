"""Tests for codex scroll simulation components."""
import sys
import pathlib

# Add codex/src to path to allow importing the modules
# This matches the pattern used in other test files in this repository
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "codex" / "src"))

from models.scroll import Scroll, RoutingHeader, Provenance
from core.state import CodexState, init_state
from core.bus import CodexBus
from agents.t0_spartan import validate_raw, create_t0_scroll, t0_spartan_node
from shells.facilitator import facilitator_node
from shells.orchestrator import orchestrator_node
from graph.simulation import build_graph


def test_scroll_hash_payload():
    """Test that hash_payload produces consistent SHA-256 hashes."""
    payload1 = {"source": "test", "content": "data", "facts": ["a", "b"]}
    payload2 = {"source": "test", "content": "data", "facts": ["a", "b"]}
    payload3 = {"source": "test", "content": "different", "facts": ["a", "b"]}
    
    hash1 = Scroll.hash_payload(payload1)
    hash2 = Scroll.hash_payload(payload2)
    hash3 = Scroll.hash_payload(payload3)
    
    # Same payload should produce same hash
    assert hash1 == hash2
    # Different payload should produce different hash
    assert hash1 != hash3
    # Hash should be 64 hex characters (SHA-256)
    assert len(hash1) == 64


def test_validate_raw_valid():
    """Test validation of valid raw payload."""
    raw = {
        "source": "test-source",
        "content": {"title": "Test"},
        "facts": ["fact1", "fact2"]
    }
    diag = validate_raw(raw)
    
    assert diag["schema_ok"] is True
    assert diag["facts_ok"] is True
    assert len(diag["missing"]) == 0


def test_validate_raw_missing_fields():
    """Test validation of payload with missing fields."""
    raw = {
        "source": "test-source"
        # missing "content" and "facts"
    }
    diag = validate_raw(raw)
    
    assert diag["schema_ok"] is False
    assert "content" in diag["missing"]
    assert "facts" in diag["missing"]


def test_validate_raw_invalid_facts():
    """Test validation of payload with invalid facts type."""
    raw = {
        "source": "test-source",
        "content": {"title": "Test"},
        "facts": "not-a-list"  # should be a list
    }
    diag = validate_raw(raw)
    
    assert diag["facts_ok"] is False


def test_create_t0_scroll_valid():
    """Test creation of T0 scroll from valid payload."""
    raw = {
        "source": "test-source",
        "content": {"title": "Test"},
        "facts": ["fact1"]
    }
    scroll = create_t0_scroll(raw, "test-corr-id")
    
    assert scroll.header.tier == "T0"
    assert scroll.header.kind == "VALIDATED"
    assert scroll.header.correlation_id == "test-corr-id"
    assert scroll.provenance.actor == "T0_SPARTAN_CORE"
    assert scroll.diagnostics["schema_ok"] is True


def test_create_t0_scroll_invalid():
    """Test creation of T0 scroll from invalid payload."""
    raw = {
        "source": "test-source"
        # missing required fields
    }
    scroll = create_t0_scroll(raw, "test-corr-id")
    
    assert scroll.header.tier == "T0"
    assert scroll.header.kind == "INIT"  # not VALIDATED
    assert scroll.diagnostics["schema_ok"] is False


def test_init_state():
    """Test state initialization."""
    scroll = Scroll(
        id="test-id",
        header=RoutingHeader(tier="T0", kind="INIT", correlation_id="test-corr"),
        payload={"test": "data"},
        provenance=Provenance(source="test", actor="test", content_hash="hash")
    )
    state = init_state(scroll)
    
    assert len(state["inbox"]) == 1
    assert state["inbox"][0].id == "test-id"
    assert len(state["ledger"]) == 0
    assert len(state["logs"]) == 0
    assert state["route"] == "T0"


def test_codex_bus():
    """Test event bus subscription and publishing."""
    bus = CodexBus()
    events_received = []
    
    def handler(msg):
        events_received.append(msg)
    
    bus.subscribe("test-topic", handler)
    bus.publish("test-topic", "test-message")
    
    assert len(events_received) == 1
    assert events_received[0] == "test-message"


def test_t0_spartan_node_valid():
    """Test T0 Spartan node with valid scroll."""
    raw = {
        "source": "test-source",
        "content": {"title": "Test"},
        "facts": ["fact1"]
    }
    scroll = Scroll(
        id="test-id",
        header=RoutingHeader(tier="T0", kind="INIT", correlation_id="test-corr"),
        payload={"raw": raw},
        provenance=Provenance(source="test", actor="test", content_hash="hash")
    )
    state = init_state(scroll)
    
    result = t0_spartan_node(state)
    
    # Should be routed to T1
    assert result["route"] == "T1"
    # Should be added to ledger
    assert len(result["ledger"]) == 1
    # Inbox should be empty
    assert len(result["inbox"]) == 0
    # Should have logs
    assert any("[T0] validated" in log for log in result["logs"])


def test_t0_spartan_node_invalid():
    """Test T0 Spartan node with invalid scroll."""
    raw = {
        "source": "test-source"
        # missing required fields
    }
    scroll = Scroll(
        id="test-id",
        header=RoutingHeader(tier="T0", kind="INIT", correlation_id="test-corr"),
        payload={"raw": raw},
        provenance=Provenance(source="test", actor="test", content_hash="hash")
    )
    state = init_state(scroll)
    
    result = t0_spartan_node(state)
    
    # Should stay at T0
    assert result["route"] == "T0"
    # Should have validation failure log
    assert any("[T0] validation failed" in log for log in result["logs"])


def test_facilitator_node():
    """Test Facilitator node."""
    scroll = Scroll(
        id="test-id",
        header=RoutingHeader(tier="T0", kind="INIT", correlation_id="test-corr"),
        payload={"test": "data"},
        provenance=Provenance(source="test", actor="test", content_hash="hash")
    )
    state = init_state(scroll)
    
    result = facilitator_node(state)
    
    # Should set route to T0
    assert result["route"] == "T0"
    # Should have received log
    assert any("[Facilitator] received scroll" in log for log in result["logs"])


def test_orchestrator_node():
    """Test Orchestrator node."""
    scroll = Scroll(
        id="test-id",
        header=RoutingHeader(tier="T0", kind="INIT", correlation_id="test-corr"),
        payload={"test": "data"},
        provenance=Provenance(source="test", actor="test", content_hash="hash")
    )
    state = init_state(scroll)
    state["route"] = "T0"
    
    result = orchestrator_node(state)
    
    # Should have dispatch log
    assert any("[Orchestrator] dispatch -> T0_Spartan" in log for log in result["logs"])


def test_full_graph_flow():
    """Test complete graph execution from seed to T1 routing."""
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
    
    graph = build_graph()
    state = init_state(initial)
    
    # Execute 4 steps: Facilitator -> Orchestrator -> T0_Spartan -> Orchestrator
    # This is enough to complete validation and route to T1
    STEPS_TO_T1_ROUTING = 4
    for _ in range(STEPS_TO_T1_ROUTING):
        state = graph.invoke(state)
    
    # Should have ledger entry
    assert len(state["ledger"]) > 0
    
    # Last ledger entry should be from T0 routing to T1
    last = state["ledger"][-1]
    assert last.header.tier == "T0"
    assert last.header.route_to == "T1"
    assert last.diagnostics["schema_ok"] is True
    
    # Should have expected logs
    logs_str = " ".join(state["logs"])
    assert "[Facilitator] received scroll" in logs_str
    assert "[Orchestrator] dispatch -> T0_Spartan" in logs_str
    assert "[T0] validated; routing to T1" in logs_str
    assert "[Orchestrator] dispatch -> T1_Sentinel (stub)" in logs_str
