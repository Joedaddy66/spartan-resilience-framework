"""
Control Plane API for Spartan Resilience Framework.
Integrates with OPA for FinOps policy enforcement.
"""
import os
import hmac
import hashlib
import json
from datetime import datetime
from typing import Dict, Any, Optional
from flask import Flask, request, jsonify
import requests

# Import telemetry
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from packages.telemetry.resource_monitor import ResourceMonitor

app = Flask(__name__)

# Security: HMAC secret for event log integrity
# MUST be replaced with a strong secret in production via environment variable
SECRET = os.getenv("SAVE_HMAC_SECRET")
if not SECRET:
    raise ValueError(
        "SAVE_HMAC_SECRET environment variable must be set. "
        "Generate a strong secret with: python -c 'import secrets; print(secrets.token_hex(32))'"
    )

# OPA endpoint configuration
OPA_URL = os.getenv("OPA_URL", "http://localhost:8181")
POLICY_PATH = os.getenv("POLICY_PATH", "finops")

# Telemetry
telemetry = ResourceMonitor()


def sign_event(event: Dict[str, Any]) -> str:
    """
    Sign an event with HMAC for append-only log integrity.
    
    Args:
        event: Event dictionary
        
    Returns:
        HMAC signature (hex)
    """
    event_json = json.dumps(event, sort_keys=True)
    signature = hmac.new(
        SECRET.encode(),
        event_json.encode(),
        hashlib.sha256
    ).hexdigest()
    return signature


def verify_event(event: Dict[str, Any], signature: str) -> bool:
    """
    Verify event signature.
    
    Args:
        event: Event dictionary
        signature: Expected HMAC signature
        
    Returns:
        True if signature is valid
    """
    expected = sign_event(event)
    return hmac.compare_digest(expected, signature)


def check_policy_opa(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check policy using OPA endpoint.
    
    Args:
        payload: Input data for policy evaluation
        
    Returns:
        Policy decision with allow/deny/warn
    """
    try:
        opa_endpoint = f"{OPA_URL}/v1/data/{POLICY_PATH}"
        response = requests.post(
            opa_endpoint,
            json={"input": payload},
            timeout=5
        )
        response.raise_for_status()
        result = response.json()
        
        # Extract policy decision
        policy_result = result.get("result", {})
        
        return {
            "allowed": policy_result.get("allow", False),
            "deny_messages": policy_result.get("deny", []),
            "warn_messages": policy_result.get("warn", []),
        }
    except requests.RequestException as e:
        # If OPA is unavailable, fail closed for security
        return {
            "allowed": False,
            "deny_messages": [f"Policy service unavailable: {str(e)}"],
            "warn_messages": [],
        }


def check_policy_embedded(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check policy using embedded logic (fallback if OPA unavailable).
    This implements the core FinOps rules directly.
    
    Args:
        payload: Input data for policy evaluation
        
    Returns:
        Policy decision with allow/deny/warn
    """
    deny_messages = []
    warn_messages = []
    
    # Budget guardrail
    if payload.get("unit_cost_usd", 0) > 0.5:
        deny_messages.append(
            f"Unit cost {payload['unit_cost_usd']:.4f} exceeds budget cap of 0.5 USD"
        )
    elif payload.get("unit_cost_usd", 0) > 0.3:
        warn_messages.append(
            f"Warning: Unit cost {payload['unit_cost_usd']:.4f} is approaching budget cap"
        )
    
    # Total spend check
    if payload.get("total_spend_usd", 0) > payload.get("budget_cap_usd", float('inf')):
        deny_messages.append(
            f"Total spend {payload['total_spend_usd']:.2f} USD exceeds budget cap {payload['budget_cap_usd']:.2f} USD"
        )
    
    # Cost tags requirement
    cost_tags = payload.get("cost_tags")
    if not cost_tags:
        deny_messages.append("Deployment missing required cost_tags")
    elif isinstance(cost_tags, dict):
        if not cost_tags.get("team"):
            deny_messages.append("cost_tags missing required 'team' field")
        if not cost_tags.get("environment"):
            deny_messages.append("cost_tags missing required 'environment' field")
    
    # Promotion checks
    if payload.get("promotion_request"):
        if payload.get("test_pass_rate", 0) < 0.95:
            deny_messages.append(
                f"Cannot promote: test pass rate {payload['test_pass_rate']*100:.2f}% is below required 95%"
            )
        if not payload.get("security_scan_passed", False):
            deny_messages.append("Cannot promote: security scan failed")
    
    # Carbon intensity check
    carbon_intensity = payload.get("carbon_intensity_g_per_kwh", 0)
    if carbon_intensity > 400:
        deny_messages.append(
            f"Carbon intensity {carbon_intensity:.2f} g/kWh exceeds limit of 400 g/kWh"
        )
    elif carbon_intensity > 300:
        warn_messages.append(
            f"Warning: Carbon intensity {carbon_intensity:.2f} g/kWh is high - consider optimization"
        )
    
    # Carbon efficient region check
    region = payload.get("deployment_region")
    if region and region not in ["us-west-2", "eu-north-1", "ca-central-1"]:
        deny_messages.append(
            f"Region '{region}' is not carbon-efficient - consider shifting to a greener region"
        )
    
    return {
        "allowed": len(deny_messages) == 0,
        "deny_messages": deny_messages,
        "warn_messages": warn_messages,
    }


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "timestamp": datetime.now(datetime.UTC).isoformat() if hasattr(datetime, 'UTC') else datetime.utcnow().isoformat()})


@app.route("/v1/gates/policy-check", methods=["POST"])
def policy_check():
    """
    FinOps policy gate endpoint.
    Evaluates deployment requests against FinOps policies using OPA.
    """
    payload = request.get_json()
    
    if not payload:
        return jsonify({"error": "Invalid request body"}), 400
    
    # Try OPA first, fall back to embedded logic
    use_opa = os.getenv("USE_OPA", "true").lower() == "true"
    
    if use_opa:
        decision = check_policy_opa(payload)
    else:
        decision = check_policy_embedded(payload)
    
    # Log event with signature for provenance
    event = {
        "timestamp": datetime.now(datetime.UTC).isoformat() if hasattr(datetime, 'UTC') else datetime.utcnow().isoformat(),
        "type": "policy_check",
        "payload": payload,
        "decision": decision,
    }
    signature = sign_event(event)
    event["signature"] = signature
    
    # Return decision
    response = {
        "allowed": decision["allowed"],
        "deny_messages": decision["deny_messages"],
        "warn_messages": decision["warn_messages"],
        "event_signature": signature,
    }
    
    status_code = 200 if decision["allowed"] else 403
    return jsonify(response), status_code


@app.route("/v1/metrics/inference", methods=["POST"])
def log_inference_metrics():
    """
    Log inference metrics endpoint.
    Receives real-time metrics from model instances.
    """
    payload = request.get_json()
    
    if not payload:
        return jsonify({"error": "Invalid request body"}), 400
    
    # Validate required fields
    required_fields = ["model", "input_tokens", "output_tokens", "duration_ms"]
    for field in required_fields:
        if field not in payload:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    
    # Log metrics
    metrics = telemetry.log_inference(
        model=payload["model"],
        input_tokens=payload["input_tokens"],
        output_tokens=payload["output_tokens"],
        duration_ms=payload["duration_ms"],
        metadata=payload.get("metadata"),
    )
    
    return jsonify({"status": "logged", "metrics": metrics}), 201


@app.route("/v1/metrics/training", methods=["POST"])
def log_training_metrics():
    """
    Log training job metrics endpoint.
    """
    payload = request.get_json()
    
    if not payload:
        return jsonify({"error": "Invalid request body"}), 400
    
    # Validate required fields
    required_fields = ["model", "duration_hours"]
    for field in required_fields:
        if field not in payload:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    
    # Log metrics
    metrics = telemetry.log_training(
        model=payload["model"],
        duration_hours=payload["duration_hours"],
        gpu_count=payload.get("gpu_count", 1),
        metadata=payload.get("metadata"),
    )
    
    return jsonify({"status": "logged", "metrics": metrics}), 201


@app.route("/v1/metrics", methods=["GET"])
def get_metrics():
    """Get all collected metrics."""
    return jsonify({"metrics": telemetry.get_metrics()})


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    debug = os.getenv("DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
