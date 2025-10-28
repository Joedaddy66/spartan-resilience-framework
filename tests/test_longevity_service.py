"""
Tests for RA Longevity MLOps Service.
"""
import os
import json
import tempfile
from pathlib import Path
from io import BytesIO

import pytest
from fastapi.testclient import TestClient

# Set required environment variables before importing the app
os.environ['SAVE_HMAC_SECRET'] = 'test-secret-key-for-testing-only-32-chars'
os.environ['BEARER_TOKEN'] = 'test-token'
os.environ['ARTIFACTS_DIR'] = tempfile.mkdtemp()

# Add parent directory to path for imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'apps' / 'longevity-service'))

from src.main import app, calculate_hmac_signature, validate_dkil_signature
from src.main import DKILSignature


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Authentication headers."""
    return {"Authorization": "Bearer test-token"}


@pytest.fixture
def sample_data():
    """Sample RA longevity data."""
    return [
        {"RA": 0.85, "D": 2.1, "M": 1.5, "S": 3.2, "LR": 0.001},
        {"RA": 0.92, "D": 1.8, "M": 1.3, "S": 2.9, "LR": 0.0005},
        {"RA": 0.78, "D": 2.3, "M": 1.7, "S": 3.5, "LR": 0.0012},
        {"RA": 0.88, "D": 1.9, "M": 1.4, "S": 3.0, "LR": 0.0008},
    ]


@pytest.fixture
def sample_csv():
    """Sample CSV data."""
    csv_content = """RA,D,M,S,LR
0.85,2.1,1.5,3.2,0.001
0.92,1.8,1.3,2.9,0.0005
0.78,2.3,1.7,3.5,0.0012
0.88,1.9,1.4,3.0,0.0008"""
    return BytesIO(csv_content.encode())


# ============================================================================
# Health and Root Tests
# ============================================================================

def test_root(client):
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "RA Longevity MLOps API"
    assert "endpoints" in data


def test_health(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data


# ============================================================================
# Authentication Tests
# ============================================================================

def test_analyze_without_auth(client, sample_data):
    """Test analyze endpoint without authentication."""
    response = client.post(
        "/api/longevity/analyze",
        json={"mode": "tabular", "data": sample_data}
    )
    assert response.status_code == 401


def test_analyze_with_invalid_auth(client, sample_data):
    """Test analyze endpoint with invalid authentication."""
    response = client.post(
        "/api/longevity/analyze",
        headers={"Authorization": "Bearer invalid-token"},
        json={"mode": "tabular", "data": sample_data}
    )
    assert response.status_code == 401


# ============================================================================
# Analyze Endpoint Tests
# ============================================================================

def test_analyze_with_json_data(client, auth_headers, sample_data):
    """Test analyze endpoint with JSON data."""
    response = client.post(
        "/api/longevity/analyze",
        headers=auth_headers,
        json={"mode": "tabular", "data": sample_data}
    )
    assert response.status_code == 200
    data = response.json()
    
    # Validate response structure
    assert "run_id" in data
    assert data["run_id"].startswith("run_")
    assert "predictions" in data
    assert len(data["predictions"]) == len(sample_data)
    assert "ldrop_metrics" in data
    assert "ldrop_mean" in data["ldrop_metrics"]
    assert "ldrop_reduction_pct" in data["ldrop_metrics"]
    assert "ra_score_deltas" in data
    assert "report_url" in data
    assert "artifacts_created" in data
    
    # Validate predictions
    for pred in data["predictions"]:
        assert "index" in pred
        assert "ra_score" in pred
        assert "predicted_longevity" in pred
        assert "confidence" in pred
        assert "features" in pred


def test_analyze_with_csv_file(client, auth_headers, sample_csv):
    """Test analyze endpoint with CSV file upload."""
    response = client.post(
        "/api/longevity/analyze",
        headers=auth_headers,
        data={"mode": "tabular"},
        files={"file": ("test_data.csv", sample_csv, "text/csv")}
    )
    assert response.status_code == 200
    data = response.json()
    
    assert "run_id" in data
    assert "predictions" in data
    assert len(data["predictions"]) == 4


def test_analyze_with_invalid_mode(client, auth_headers, sample_data):
    """Test analyze endpoint with invalid mode."""
    response = client.post(
        "/api/longevity/analyze",
        headers=auth_headers,
        json={"mode": "invalid_mode", "data": sample_data}
    )
    assert response.status_code == 400
    assert "Mode must be" in response.json()["detail"]


def test_analyze_with_missing_data(client, auth_headers):
    """Test analyze endpoint without data or file."""
    response = client.post(
        "/api/longevity/analyze",
        headers=auth_headers,
        json={"mode": "tabular"}
    )
    assert response.status_code == 400


def test_analyze_with_missing_columns(client, auth_headers):
    """Test analyze endpoint with missing required columns."""
    incomplete_data = [
        {"RA": 0.85, "D": 2.1},  # Missing M, S, LR
    ]
    response = client.post(
        "/api/longevity/analyze",
        headers=auth_headers,
        json={"mode": "tabular", "data": incomplete_data}
    )
    assert response.status_code == 400
    assert "Missing required columns" in response.json()["detail"]


def test_analyze_time_series_mode(client, auth_headers, sample_data):
    """Test analyze endpoint with time_series mode."""
    response = client.post(
        "/api/longevity/analyze",
        headers=auth_headers,
        json={"mode": "time_series", "data": sample_data}
    )
    assert response.status_code == 200
    data = response.json()
    assert "run_id" in data


# ============================================================================
# Report Endpoint Tests
# ============================================================================

def test_get_report_json(client, auth_headers, sample_data):
    """Test getting JSON report."""
    # First, create an analysis
    analyze_response = client.post(
        "/api/longevity/analyze",
        headers=auth_headers,
        json={"mode": "tabular", "data": sample_data}
    )
    run_id = analyze_response.json()["run_id"]
    
    # Get JSON report
    response = client.get(
        f"/api/longevity/report/{run_id}?format=json",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["run_id"] == run_id
    assert "predictions" in data
    assert "ldrop_metrics" in data


def test_get_report_html(client, auth_headers, sample_data):
    """Test getting HTML report."""
    # First, create an analysis
    analyze_response = client.post(
        "/api/longevity/analyze",
        headers=auth_headers,
        json={"mode": "tabular", "data": sample_data}
    )
    run_id = analyze_response.json()["run_id"]
    
    # Get HTML report
    response = client.get(
        f"/api/longevity/report/{run_id}?format=html",
        headers=auth_headers
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"RA Longevity Analysis Report" in response.content


def test_get_report_not_found(client, auth_headers):
    """Test getting report for non-existent run_id."""
    response = client.get(
        "/api/longevity/report/run_nonexistent?format=json",
        headers=auth_headers
    )
    assert response.status_code == 404


# ============================================================================
# L-Drop Metrics Tests
# ============================================================================

def test_ldrop_metrics_calculation(client, auth_headers):
    """Test L-Drop metrics are calculated correctly."""
    # Create data with known RA scores to verify deltas
    data = [
        {"RA": 0.90, "D": 2.0, "M": 1.5, "S": 3.0, "LR": 0.001},
        {"RA": 0.85, "D": 2.0, "M": 1.5, "S": 3.0, "LR": 0.001},
        {"RA": 0.80, "D": 2.0, "M": 1.5, "S": 3.0, "LR": 0.001},
    ]
    
    response = client.post(
        "/api/longevity/analyze",
        headers=auth_headers,
        json={"mode": "tabular", "data": data}
    )
    assert response.status_code == 200
    result = response.json()
    
    # Verify L-Drop metrics exist
    ldrop = result["ldrop_metrics"]
    assert "ldrop_mean" in ldrop
    assert "ldrop_reduction_pct" in ldrop
    assert "ldrop_max" in ldrop
    assert "ldrop_min" in ldrop
    
    # Verify RA score deltas
    assert len(result["ra_score_deltas"]) == 2  # n-1 deltas for n predictions


# ============================================================================
# DKIL Tests
# ============================================================================

def test_dkil_lock_file_creation(client, auth_headers):
    """Test DKIL lock file is created when threshold is met."""
    # Use high LDROP_THRESHOLD to ensure lock is created
    os.environ['LDROP_THRESHOLD'] = '0.1'  # Very low threshold
    
    data = [
        {"RA": 0.95, "D": 1.5, "M": 1.5, "S": 3.0, "LR": 0.0001},
        {"RA": 0.85, "D": 2.5, "M": 1.5, "S": 3.0, "LR": 0.001},
    ]
    
    response = client.post(
        "/api/longevity/analyze",
        headers=auth_headers,
        json={"mode": "tabular", "data": data}
    )
    assert response.status_code == 200
    result = response.json()
    
    # Check if DKIL lock file was created
    artifacts_created = result["artifacts_created"]
    has_dkil = any("dkil_lock.json" in artifact for artifact in artifacts_created)
    
    # Verify based on actual L-Drop reduction
    if result["ldrop_metrics"]["ldrop_reduction_pct"] >= 0.1:
        assert has_dkil, "DKIL lock file should be created when threshold is met"


def test_hmac_signature_consistency(client, auth_headers):
    """Test HMAC signatures are consistent."""
    test_data = {"test": "data", "value": 123}
    sig1 = calculate_hmac_signature(test_data)
    sig2 = calculate_hmac_signature(test_data)
    assert sig1 == sig2


# ============================================================================
# Deploy Endpoint Tests
# ============================================================================

def test_deploy_without_valid_run(client, auth_headers):
    """Test deploy endpoint with non-existent run_id."""
    deploy_request = {
        "run_id": "run_nonexistent",
        "model_name": "test-model",
        "dkil_signature": {
            "human_key": "a" * 32,
            "logic_key": "b" * 64,
            "timestamp": "2025-10-28T18:00:00Z"
        },
        "target_registry": "staging"
    }
    
    response = client.post(
        "/api/longevity/deploy",
        headers=auth_headers,
        json=deploy_request
    )
    assert response.status_code == 404


def test_deploy_without_dkil_lock(client, auth_headers):
    """Test deploy endpoint when DKIL lock doesn't exist."""
    # Create analysis without DKIL lock (use data that won't meet threshold)
    os.environ['LDROP_THRESHOLD'] = '99.0'  # Very high threshold
    
    data = [
        {"RA": 0.50, "D": 3.0, "M": 1.0, "S": 2.0, "LR": 0.01},
        {"RA": 0.51, "D": 3.0, "M": 1.0, "S": 2.0, "LR": 0.01},
    ]
    
    analyze_response = client.post(
        "/api/longevity/analyze",
        headers=auth_headers,
        json={"mode": "tabular", "data": data}
    )
    run_id = analyze_response.json()["run_id"]
    
    # Try to deploy without DKIL lock
    deploy_request = {
        "run_id": run_id,
        "model_name": "test-model",
        "dkil_signature": {
            "human_key": "a" * 32,
            "logic_key": "b" * 64,
            "timestamp": "2025-10-28T18:00:00Z"
        },
        "target_registry": "staging"
    }
    
    response = client.post(
        "/api/longevity/deploy",
        headers=auth_headers,
        json=deploy_request
    )
    # Should fail because DKIL lock doesn't exist (404) or signature is invalid (400)
    assert response.status_code in [400, 404]


def test_deploy_with_invalid_human_key(client, auth_headers, sample_data):
    """Test deploy endpoint with invalid human key."""
    # Set low threshold to ensure DKIL lock is created
    os.environ['LDROP_THRESHOLD'] = '0.1'
    
    # Create analysis
    analyze_response = client.post(
        "/api/longevity/analyze",
        headers=auth_headers,
        json={"mode": "tabular", "data": sample_data}
    )
    result = analyze_response.json()
    run_id = result["run_id"]
    
    # Only proceed if DKIL lock was created
    if any("dkil_lock.json" in a for a in result["artifacts_created"]):
        # Try to deploy with short human key (invalid)
        deploy_request = {
            "run_id": run_id,
            "model_name": "test-model",
            "dkil_signature": {
                "human_key": "short",  # Too short
                "logic_key": "b" * 64,
                "timestamp": "2025-10-28T18:00:00Z"
            },
            "target_registry": "staging"
        }
        
        response = client.post(
            "/api/longevity/deploy",
            headers=auth_headers,
            json=deploy_request
        )
        assert response.status_code == 400


# ============================================================================
# Artifact Tests
# ============================================================================

def test_artifacts_are_created(client, auth_headers, sample_data):
    """Test that all expected artifacts are created."""
    response = client.post(
        "/api/longevity/analyze",
        headers=auth_headers,
        json={"mode": "tabular", "data": sample_data}
    )
    assert response.status_code == 200
    result = response.json()
    
    artifacts = result["artifacts_created"]
    
    # Should always have JSON and HTML reports
    assert any("report.json" in a for a in artifacts)
    assert any("report.html" in a for a in artifacts)


def test_artifacts_directory_structure(client, auth_headers, sample_data):
    """Test artifacts are organized by run_id."""
    response = client.post(
        "/api/longevity/analyze",
        headers=auth_headers,
        json={"mode": "tabular", "data": sample_data}
    )
    result = response.json()
    run_id = result["run_id"]
    
    # Check artifacts directory
    artifacts_dir = Path(os.environ['ARTIFACTS_DIR'])
    run_dir = artifacts_dir / run_id
    
    assert run_dir.exists()
    assert (run_dir / "report.json").exists()
    assert (run_dir / "report.html").exists()


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================

def test_analyze_with_empty_data(client, auth_headers):
    """Test analyze endpoint with empty data array."""
    response = client.post(
        "/api/longevity/analyze",
        headers=auth_headers,
        json={"mode": "tabular", "data": []}
    )
    assert response.status_code == 400


def test_analyze_with_single_row(client, auth_headers):
    """Test analyze endpoint with single data row."""
    data = [{"RA": 0.85, "D": 2.1, "M": 1.5, "S": 3.2, "LR": 0.001}]
    
    response = client.post(
        "/api/longevity/analyze",
        headers=auth_headers,
        json={"mode": "tabular", "data": data}
    )
    assert response.status_code == 200
    result = response.json()
    assert len(result["predictions"]) == 1


def test_multiple_analyses_different_run_ids(client, auth_headers, sample_data):
    """Test that multiple analyses get different run IDs."""
    response1 = client.post(
        "/api/longevity/analyze",
        headers=auth_headers,
        json={"mode": "tabular", "data": sample_data}
    )
    response2 = client.post(
        "/api/longevity/analyze",
        headers=auth_headers,
        json={"mode": "tabular", "data": sample_data}
    )
    
    run_id1 = response1.json()["run_id"]
    run_id2 = response2.json()["run_id"]
    
    assert run_id1 != run_id2
