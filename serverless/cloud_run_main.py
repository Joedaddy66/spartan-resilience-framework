"""
Flask stub for LeonideX RSA audit endpoint.
This is a public-safe simulation - no formulas, dataset rows, or internal metrics.
"""
from flask import Flask, request, jsonify
import hashlib
import json
from datetime import datetime, timezone

app = Flask(__name__)


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'service': 'leonidex-audit-stub'
    }), 200


@app.route('/audit', methods=['POST'])
def audit():
    """
    RSA audit endpoint that returns a simulated PASS result.

    Public-safe: only returns decision (PASS/FAIL) and depth_floor_shown.
    No formulas, no dataset rows, no internal metrics.
    """
    try:
        # Validate authorization header
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({
                'schema': 'leonidex-audit-v1',
                'decision': 'FAIL',
                'error': 'Missing or invalid authorization',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }), 401

        # Get request data
        data = request.get_json() or {}
        pubkey_path = data.get('pubkey_path', 'keys/sample.pub')

        # Generate a deterministic fingerprint for the request
        request_str = json.dumps(data, sort_keys=True)
        fingerprint = hashlib.sha256(request_str.encode()).hexdigest()[:16]

        # Simulate FAIL case for testing
        decision = 'PASS'
        if 'test_fail' in pubkey_path.lower() or data.get('simulate_fail', False):
            decision = 'FAIL'

        # Simulated audit result
        result = {
            'schema': 'leonidex-audit-v1',
            'decision': decision,
            'depth_floor_shown': 'Depth ≥ threshold' if decision == 'PASS' else 'Depth < threshold',
            'fingerprint': fingerprint,
            'report_hash': hashlib.sha256(fingerprint.encode()).hexdigest(),
            'signature': 'simulated_signature_' + fingerprint[:8],
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'pubkey_path': pubkey_path
        }

        status_code = 200 if decision == 'PASS' else 422
        return jsonify(result), status_code

    except Exception as e:
        # Return generic error message for security
        return jsonify({
            'schema': 'leonidex-audit-v1',
            'decision': 'FAIL',
            'error': 'Internal server error',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
