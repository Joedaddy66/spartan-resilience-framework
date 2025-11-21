# Codex: Scroll Flow Simulation

This directory contains a minimal, auditable LangGraph-based simulation of scroll flow between tiers in the Spartan Resilience Framework.

## Overview

The Codex system simulates a multi-tier validation and processing pipeline where "scrolls" (data packets) flow through different tiers of agents:

- **T0 (Spartans)**: Initial validation of schema, content hash, and basic facts
- **T1 (Sentinels)**: Policy checks and enrichment (stub)
- **T2 (Council)**: Final review and approval (stub)

## Directory Structure

```
codex/
  README.md
  requirements.txt
  config/tiers.yaml              # tier configuration
  docs/scroll_format.md          # scroll data structure documentation
  src/
    __init__.py
    models/scroll.py             # Scroll, RoutingHeader, Provenance models
    core/state.py                # CodexState for LangGraph
    core/bus.py                  # simple event bus (future use)
    agents/t0_spartan.py         # T0 validation agent
    shells/facilitator.py        # Facilitator shell
    shells/orchestrator.py       # Orchestrator shell
    graph/simulation.py          # LangGraph workflow
    run_sim.py                   # demo runner
```

## Installation

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Running the Simulation

```bash
cd src
python -m run_sim
```

Expected output:
```
--- LOGS ---
[Facilitator] received scroll seed-0001 tier=T0 kind=INIT
[Orchestrator] dispatch -> T0_Spartan
[T0] validated; routing to T1
[Orchestrator] dispatch -> T1_Sentinel (stub)

--- LEDGER (last) ---
id: <uuid> tier: T0 route_to: T1
diagnostics: {'schema_ok': True, 'missing': [], 'facts_ok': True}
```

## Key Components

### Scroll Data Model

A scroll contains:
- **header**: Routing metadata (tier, kind, route_to, correlation_id)
- **payload**: Actual data being processed
- **provenance**: Origin and integrity (source, actor, content_hash, signatures)
- **diagnostics**: Validation results

See `docs/scroll_format.md` for detailed specification.

### LangGraph Flow

1. **Facilitator**: Receives incoming scroll, stamps correlation ID
2. **Orchestrator**: Routes to appropriate tier based on state
3. **T0_Spartan**: Validates schema and facts, promotes to T1 or rejects
4. Loop back to Orchestrator for next routing decision

### Deterministic Audit

- All processed scrolls are appended to the ledger
- Content hashes anchor payload integrity
- Logs trace all state transitions

## Extending the System

### Add T1 Sentinel Node

Create `src/agents/t1_sentinel.py`:
```python
def t1_sentinel_node(state):
    # Review T0 diagnostics
    # Apply policy checks
    # Sign and promote to T2 or bounce back
    pass
```

Register in `src/graph/simulation.py`:
```python
graph.add_node("T1_Sentinel", t1_sentinel_node)
# Update route_selector to route T1 -> T1_Sentinel
```

### Add Cryptographic Signatures

Replace `signatures: []` in `Provenance` with actual ed25519 signatures:
```python
from cryptography.hazmat.primitives.asymmetric import ed25519

# In agent code:
private_key = ed25519.Ed25519PrivateKey.generate()
signature = private_key.sign(content_hash.encode())
provenance.signatures.append({
    "algo": "ed25519",
    "pubkey": base64.b64encode(private_key.public_key().public_bytes(...)),
    "sig": base64.b64encode(signature)
})
```

### Add Queue Backend

Replace `core/bus.py` with Redis Pub/Sub or message queue:
```python
import redis
r = redis.Redis(host='localhost', port=6379)
r.publish('scroll.t0', json.dumps(scroll.dict()))
```

### Add HTTP API

Wrap Facilitator + Orchestrator in FastAPI:
```python
from fastapi import FastAPI
app = FastAPI()

@app.post("/v1/scrolls")
async def submit_scroll(scroll: Scroll):
    state = init_state(scroll)
    result = graph.invoke(state)
    return {"ledger": result["ledger"]}
```

## Configuration

Edit `config/tiers.yaml` to add/modify tiers and validation rules.

## Testing

The simulation is minimal and runs locally. For production use:
- Add proper error handling
- Implement retry logic
- Add monitoring and metrics
- Deploy on VM or container platform
- Add authentication and authorization

## License

Part of the Spartan Resilience Framework. See repository LICENSE.
