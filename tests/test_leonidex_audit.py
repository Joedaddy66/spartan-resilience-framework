"""Tests for LeonideX RSA audit serverless endpoint."""
import json
import pytest
import sys
from pathlib import Path

# Add serverless directory to path
serverless_path = Path(__file__).parent.parent / 'serverless'
sys.path.insert(0, str(serverless_path))

from cloud_run_main import app


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_health_endpoint(client):
    """Test the /health endpoint returns healthy status."""
    response = client.get('/health')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['status'] == 'healthy'
    assert 'timestamp' in data
    assert data['service'] == 'leonidex-audit-stub'


def test_audit_endpoint_success(client):
    """Test the /audit endpoint returns PASS decision."""
    payload = {
        'pubkey_path': 'keys/sample.pub'
    }

    response = client.post('/audit',
                          data=json.dumps(payload),
                          content_type='application/json',
                          headers={'Authorization': 'Bearer test-token'})

    assert response.status_code == 200

    data = json.loads(response.data)
    assert data['schema'] == 'leonidex-audit-v1'
    assert data['decision'] == 'PASS'
    assert data['depth_floor_shown'] == 'Depth ≥ threshold'
    assert 'fingerprint' in data
    assert 'report_hash' in data
    assert 'signature' in data
    assert 'timestamp' in data
    assert data['pubkey_path'] == 'keys/sample.pub'


def test_audit_endpoint_no_payload(client):
    """Test the /audit endpoint works with no payload."""
    response = client.post('/audit',
                          data=json.dumps({}),
                          content_type='application/json',
                          headers={'Authorization': 'Bearer test-token'})

    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['decision'] == 'PASS'


def test_audit_endpoint_custom_pubkey(client):
    """Test the /audit endpoint with custom pubkey path."""
    payload = {
        'pubkey_path': 'keys/custom-key.pub'
    }

    response = client.post('/audit',
                          data=json.dumps(payload),
                          content_type='application/json',
                          headers={'Authorization': 'Bearer test-token'})

    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['pubkey_path'] == 'keys/custom-key.pub'


def test_audit_fingerprint_deterministic(client):
    """Test that fingerprints are deterministic for same input."""
    payload = {
        'pubkey_path': 'keys/test.pub',
        'extra_data': 'test123'
    }

    response1 = client.post('/audit',
                           data=json.dumps(payload),
                           content_type='application/json',
                           headers={'Authorization': 'Bearer test-token'})
    data1 = json.loads(response1.data)

    response2 = client.post('/audit',
                           data=json.dumps(payload),
                           content_type='application/json',
                           headers={'Authorization': 'Bearer test-token'})
    data2 = json.loads(response2.data)

    assert data1['fingerprint'] == data2['fingerprint']
    assert data1['report_hash'] == data2['report_hash']


def test_audit_no_internal_metrics(client):
    """Test that audit response contains no internal metrics."""
    payload = {
        'pubkey_path': 'keys/sample.pub'
    }

    response = client.post('/audit',
                          data=json.dumps(payload),
                          content_type='application/json',
                          headers={'Authorization': 'Bearer test-token'})

    data = json.loads(response.data)

    # Ensure no internal metrics are exposed
    forbidden_keys = ['raw_score', 'internal_metric', 'formula', 'dataset',
                     'threshold_value', 'actual_depth', 'computation_details']

    for key in forbidden_keys:
        assert key not in data, f"Internal metric '{key}' should not be exposed"

    # Only these public-safe fields should be present
    expected_keys = {'schema', 'decision', 'depth_floor_shown', 'fingerprint',
                    'report_hash', 'signature', 'timestamp', 'pubkey_path'}
    actual_keys = set(data.keys())

    # All expected keys should be present
    assert expected_keys.issubset(actual_keys)


def test_audit_response_format(client):
    """Test that audit response follows the expected format."""
    response = client.post('/audit',
                          data=json.dumps({'pubkey_path': 'keys/sample.pub'}),
                          content_type='application/json',
                          headers={'Authorization': 'Bearer test-token'})

    data = json.loads(response.data)

    # Verify schema version
    assert data['schema'] == 'leonidex-audit-v1'

    # Verify decision is either PASS or FAIL
    assert data['decision'] in ['PASS', 'FAIL']

    # Verify depth_floor_shown contains threshold message
    assert 'threshold' in data['depth_floor_shown'].lower()

    # Verify signature format
    assert data['signature'].startswith('simulated_signature_')


def test_audit_missing_auth(client):
    """Test that audit endpoint requires authorization."""
    payload = {
        'pubkey_path': 'keys/sample.pub'
    }

    response = client.post('/audit',
                          data=json.dumps(payload),
                          content_type='application/json')

    assert response.status_code == 401
    data = json.loads(response.data)
    assert data['decision'] == 'FAIL'
    assert 'authorization' in data['error'].lower()


def test_audit_invalid_auth(client):
    """Test that audit endpoint validates authorization format."""
    payload = {
        'pubkey_path': 'keys/sample.pub'
    }

    response = client.post('/audit',
                          data=json.dumps(payload),
                          content_type='application/json',
                          headers={'Authorization': 'InvalidFormat'})

    assert response.status_code == 401
    data = json.loads(response.data)
    assert data['decision'] == 'FAIL'


def test_audit_fail_simulation(client):
    """Test that audit can return FAIL for specific inputs."""
    payload = {
        'pubkey_path': 'keys/test_fail.pub'
    }

    response = client.post('/audit',
                          data=json.dumps(payload),
                          content_type='application/json',
                          headers={'Authorization': 'Bearer test-token'})

    assert response.status_code == 422
    data = json.loads(response.data)
    assert data['decision'] == 'FAIL'
    assert 'threshold' in data['depth_floor_shown'].lower()


def test_audit_fail_simulation_flag(client):
    """Test that audit can return FAIL using simulate_fail flag."""
    payload = {
        'pubkey_path': 'keys/sample.pub',
        'simulate_fail': True
    }

    response = client.post('/audit',
                          data=json.dumps(payload),
                          content_type='application/json',
                          headers={'Authorization': 'Bearer test-token'})

    assert response.status_code == 422
    data = json.loads(response.data)
    assert data['decision'] == 'FAIL'
