"""
Tests for control plane policy checking.
"""
import sys
import pathlib
import os
import json
import importlib.util

# Add packages to path
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

# Set required env var for import
os.environ["SAVE_HMAC_SECRET"] = "test-secret-for-unit-tests-only"

# Import from control-plane using importlib to handle hyphen in name
spec = importlib.util.spec_from_file_location(
    "main",
    str(pathlib.Path(__file__).resolve().parents[1] / "apps" / "control-plane" / "src" / "main.py")
)
main_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(main_module)

check_policy_embedded = main_module.check_policy_embedded
sign_event = main_module.sign_event
verify_event = main_module.verify_event


def test_policy_budget_cap_deny():
    """Test that exceeding budget cap is denied."""
    payload = {
        "unit_cost_usd": 0.6,
        "cost_tags": {"team": "ai", "environment": "dev"}
    }
    
    decision = check_policy_embedded(payload)
    assert decision["allowed"] is False
    assert len(decision["deny_messages"]) > 0
    assert "exceeds budget cap" in decision["deny_messages"][0]


def test_policy_budget_cap_allow():
    """Test that under budget cap is allowed."""
    payload = {
        "unit_cost_usd": 0.2,
        "cost_tags": {"team": "ai", "environment": "dev"}
    }
    
    decision = check_policy_embedded(payload)
    assert decision["allowed"] is True
    assert len(decision["deny_messages"]) == 0


def test_policy_budget_cap_warning():
    """Test that approaching budget cap generates warning."""
    payload = {
        "unit_cost_usd": 0.4,
        "cost_tags": {"team": "ai", "environment": "dev"}
    }
    
    decision = check_policy_embedded(payload)
    assert decision["allowed"] is True
    assert len(decision["warn_messages"]) > 0
    assert "approaching budget cap" in decision["warn_messages"][0]


def test_policy_missing_cost_tags():
    """Test that missing cost tags is denied."""
    payload = {
        "unit_cost_usd": 0.2
    }
    
    decision = check_policy_embedded(payload)
    assert decision["allowed"] is False
    assert any("cost_tags" in msg for msg in decision["deny_messages"])


def test_policy_missing_team_tag():
    """Test that missing team tag is denied."""
    payload = {
        "unit_cost_usd": 0.2,
        "cost_tags": {"environment": "dev"}
    }
    
    decision = check_policy_embedded(payload)
    assert decision["allowed"] is False
    assert any("team" in msg for msg in decision["deny_messages"])


def test_policy_missing_environment_tag():
    """Test that missing environment tag is denied."""
    payload = {
        "unit_cost_usd": 0.2,
        "cost_tags": {"team": "ai"}
    }
    
    decision = check_policy_embedded(payload)
    assert decision["allowed"] is False
    assert any("environment" in msg for msg in decision["deny_messages"])


def test_policy_promotion_low_test_pass_rate():
    """Test that low test pass rate blocks promotion."""
    payload = {
        "unit_cost_usd": 0.2,
        "cost_tags": {"team": "ai", "environment": "dev"},
        "promotion_request": True,
        "test_pass_rate": 0.90,
        "security_scan_passed": True
    }
    
    decision = check_policy_embedded(payload)
    assert decision["allowed"] is False
    assert any("test pass rate" in msg for msg in decision["deny_messages"])


def test_policy_promotion_failed_security_scan():
    """Test that failed security scan blocks promotion."""
    payload = {
        "unit_cost_usd": 0.2,
        "cost_tags": {"team": "ai", "environment": "dev"},
        "promotion_request": True,
        "test_pass_rate": 0.98,
        "security_scan_passed": False
    }
    
    decision = check_policy_embedded(payload)
    assert decision["allowed"] is False
    assert any("security scan" in msg for msg in decision["deny_messages"])


def test_policy_promotion_success():
    """Test that valid promotion request is allowed."""
    payload = {
        "unit_cost_usd": 0.2,
        "cost_tags": {"team": "ai", "environment": "dev"},
        "promotion_request": True,
        "test_pass_rate": 0.98,
        "security_scan_passed": True
    }
    
    decision = check_policy_embedded(payload)
    assert decision["allowed"] is True


def test_policy_high_carbon_intensity():
    """Test that high carbon intensity is denied."""
    payload = {
        "unit_cost_usd": 0.2,
        "cost_tags": {"team": "ai", "environment": "dev"},
        "carbon_intensity_g_per_kwh": 450
    }
    
    decision = check_policy_embedded(payload)
    assert decision["allowed"] is False
    assert any("Carbon intensity" in msg for msg in decision["deny_messages"])


def test_policy_carbon_intensity_warning():
    """Test that moderate carbon intensity generates warning."""
    payload = {
        "unit_cost_usd": 0.2,
        "cost_tags": {"team": "ai", "environment": "dev"},
        "carbon_intensity_g_per_kwh": 350
    }
    
    decision = check_policy_embedded(payload)
    assert decision["allowed"] is True
    assert len(decision["warn_messages"]) > 0


def test_policy_non_green_region():
    """Test that non-green region is denied."""
    payload = {
        "unit_cost_usd": 0.2,
        "cost_tags": {"team": "ai", "environment": "dev"},
        "deployment_region": "us-east-1"
    }
    
    decision = check_policy_embedded(payload)
    assert decision["allowed"] is False
    assert any("carbon-efficient" in msg for msg in decision["deny_messages"])


def test_policy_green_region():
    """Test that green region is allowed."""
    payload = {
        "unit_cost_usd": 0.2,
        "cost_tags": {"team": "ai", "environment": "dev"},
        "deployment_region": "us-west-2"
    }
    
    decision = check_policy_embedded(payload)
    assert decision["allowed"] is True


def test_event_signing():
    """Test event signing and verification."""
    event = {
        "timestamp": "2024-01-01T00:00:00",
        "type": "test",
        "data": {"key": "value"}
    }
    
    signature = sign_event(event)
    assert len(signature) == 64  # SHA256 hex is 64 chars
    
    # Verify signature
    assert verify_event(event, signature) is True
    
    # Modified event should fail verification
    modified_event = event.copy()
    modified_event["data"] = {"key": "different"}
    assert verify_event(modified_event, signature) is False


def test_event_signing_deterministic():
    """Test that event signing is deterministic."""
    event = {
        "timestamp": "2024-01-01T00:00:00",
        "type": "test",
        "data": {"key": "value"}
    }
    
    sig1 = sign_event(event)
    sig2 = sign_event(event)
    assert sig1 == sig2


def test_total_spend_check():
    """Test total spend vs budget cap."""
    payload = {
        "unit_cost_usd": 0.2,
        "cost_tags": {"team": "ai", "environment": "dev"},
        "total_spend_usd": 1000,
        "budget_cap_usd": 500
    }
    
    decision = check_policy_embedded(payload)
    assert decision["allowed"] is False
    assert any("Total spend" in msg for msg in decision["deny_messages"])
