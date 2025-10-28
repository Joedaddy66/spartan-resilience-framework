# RA Longevity MLOps Service

A FastAPI-based microservice for RA (Resource Allocation) longevity model analysis, reporting, and deployment with DKIL (Dual-Key Integrity Lock) validation.

## Features

- **Model Analysis**: Analyze tabular or time-series RA longevity data with feature encoding (RA, D, M, S, LR)
- **L-Drop Metrics**: Calculate longevity drop metrics and reduction percentages
- **Report Generation**: Automatic generation of JSON and HTML reports
- **DKIL Validation**: Dual-signature validation (human + logic keys) for secure model deployment
- **Model Registry Integration**: Deploy validated models to target registries
- **Artifact Management**: Automatic bundling and storage of analysis artifacts
- **Bearer Token Authentication**: Secure API endpoints

## API Endpoints

### 1. Analyze RA Longevity Model

```bash
POST /api/longevity/analyze
Authorization: Bearer <token>
Content-Type: multipart/form-data or application/json

# CSV Upload
curl -X POST "http://localhost:8000/api/longevity/analyze" \
  -H "Authorization: Bearer dev-token-change-in-production" \
  -F "mode=tabular" \
  -F "file=@data.csv"

# JSON Data
curl -X POST "http://localhost:8000/api/longevity/analyze" \
  -H "Authorization: Bearer dev-token-change-in-production" \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "tabular",
    "data": [
      {"RA": 0.85, "D": 2.1, "M": 1.5, "S": 3.2, "LR": 0.001},
      {"RA": 0.92, "D": 1.8, "M": 1.3, "S": 2.9, "LR": 0.0005}
    ]
  }'
```

**Response:**
```json
{
  "run_id": "run_abc123def456",
  "predictions": [...],
  "ldrop_metrics": {
    "ldrop_mean": 0.0234,
    "ldrop_reduction_pct": 76.60,
    "ldrop_max": 0.0456,
    "ldrop_min": 0.0012
  },
  "ra_score_deltas": [0.07, -0.03, ...],
  "report_url": "/api/longevity/report/run_abc123def456",
  "artifacts_created": [
    "run_abc123def456/report.json",
    "run_abc123def456/report.html",
    "run_abc123def456/dkil_lock.json"
  ]
}
```

### 2. Get Analysis Report

```bash
GET /api/longevity/report/{run_id}?format=json
Authorization: Bearer <token>

# Get JSON report
curl -X GET "http://localhost:8000/api/longevity/report/run_abc123def456?format=json" \
  -H "Authorization: Bearer dev-token-change-in-production"

# Get HTML report
curl -X GET "http://localhost:8000/api/longevity/report/run_abc123def456?format=html" \
  -H "Authorization: Bearer dev-token-change-in-production"
```

### 3. Deploy Model

```bash
POST /api/longevity/deploy
Authorization: Bearer <token>
Content-Type: application/json

curl -X POST "http://localhost:8000/api/longevity/deploy" \
  -H "Authorization: Bearer dev-token-change-in-production" \
  -H "Content-Type: application/json" \
  -d '{
    "run_id": "run_abc123def456",
    "model_name": "ra-longevity-v1",
    "dkil_signature": {
      "human_key": "human_reviewer_signature_hash_32_chars_min",
      "logic_key": "calculated_hmac_signature_of_dkil_lock_data",
      "timestamp": "2025-10-28T18:00:00Z"
    },
    "target_registry": "production"
  }'
```

**Response:**
```json
{
  "success": true,
  "model_id": "model_a1b2c3d4",
  "registry_url": "registry://production/ra-longevity-v1/model_a1b2c3d4",
  "bundle_path": "ra-longevity-v1_run_abc123def456_bundle.zip"
}
```

## Configuration

Configure via environment variables:

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `SAVE_HMAC_SECRET` | HMAC secret for event signing | - | ✅ Yes |
| `BEARER_TOKEN` | API authentication token | `dev-token-change-in-production` | ✅ Yes (production) |
| `PORT` | Server port | `8000` | No |
| `ARTIFACTS_DIR` | Artifacts storage directory | `./artifacts` | No |
| `LDROP_THRESHOLD` | L-Drop reduction threshold (%) | `5.0` | No |

### Generate HMAC Secret

```bash
python -c 'import secrets; print(secrets.token_hex(32))'
```

## Running Locally

### 1. Install Dependencies

```bash
cd apps/longevity-service
pip install -r requirements.txt
```

### 2. Set Environment Variables

```bash
export SAVE_HMAC_SECRET=$(python -c 'import secrets; print(secrets.token_hex(32))')
export BEARER_TOKEN="my-secure-token"
```

### 3. Run the Service

```bash
python src/main.py
# or
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Access the API

- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Root**: http://localhost:8000/

## Docker Deployment

### Build Image

```bash
cd apps/longevity-service
docker build -t ra-longevity-service:latest .
```

### Run Container

```bash
docker run -d \
  -p 8000:8000 \
  -e SAVE_HMAC_SECRET="your-hmac-secret" \
  -e BEARER_TOKEN="your-bearer-token" \
  -v $(pwd)/artifacts:/app/artifacts \
  --name longevity-service \
  ra-longevity-service:latest
```

## Google Cloud Run Deployment

### 1. Build and Push to Container Registry

```bash
# Set project ID
export PROJECT_ID="your-gcp-project-id"

# Build and push
gcloud builds submit --tag gcr.io/$PROJECT_ID/ra-longevity-service

# Or using Docker
docker build -t gcr.io/$PROJECT_ID/ra-longevity-service .
docker push gcr.io/$PROJECT_ID/ra-longevity-service
```

### 2. Deploy to Cloud Run

```bash
gcloud run deploy ra-longevity-service \
  --image gcr.io/$PROJECT_ID/ra-longevity-service \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars SAVE_HMAC_SECRET="your-hmac-secret",BEARER_TOKEN="your-token" \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300
```

### 3. Get Service URL

```bash
gcloud run services describe ra-longevity-service \
  --platform managed \
  --region us-central1 \
  --format 'value(status.url)'
```

## DKIL (Dual-Key Integrity Lock) Validation

DKIL ensures that model deployments are authorized by both:
1. **Human Key**: Manual review/approval signature
2. **Logic Key**: Automated validation signature (HMAC of DKIL lock data)

### Generating DKIL Signatures

#### Logic Key (Automated)

```python
import hmac
import hashlib
import json

# Read DKIL lock file
with open('artifacts/run_abc123/dkil_lock.json', 'r') as f:
    dkil_data = json.load(f)

# Calculate logic key
secret = "your-hmac-secret"
data_json = json.dumps(dkil_data, sort_keys=True)
logic_key = hmac.new(
    secret.encode(),
    data_json.encode(),
    hashlib.sha256
).hexdigest()

print(f"Logic Key: {logic_key}")
```

#### Human Key (Manual Approval)

Generate a secure signature representing human approval:

```python
import secrets
human_key = secrets.token_hex(32)
print(f"Human Key: {human_key}")
```

Store this in your approval system/database.

## Testing

### Run Tests

```bash
cd /home/runner/work/spartan-resilience-framework/spartan-resilience-framework
python -m pytest tests/test_longevity_service.py -v
```

### Example Test Data

Create a test CSV file (`test_data.csv`):

```csv
RA,D,M,S,LR
0.85,2.1,1.5,3.2,0.001
0.92,1.8,1.3,2.9,0.0005
0.78,2.3,1.7,3.5,0.0012
0.88,1.9,1.4,3.0,0.0008
```

### Manual Testing

```bash
# Test analyze endpoint
curl -X POST "http://localhost:8000/api/longevity/analyze" \
  -H "Authorization: Bearer dev-token-change-in-production" \
  -F "mode=tabular" \
  -F "file=@test_data.csv" \
  | jq .

# Save run_id from response
RUN_ID="run_abc123def456"

# Test report endpoint
curl -X GET "http://localhost:8000/api/longevity/report/$RUN_ID?format=json" \
  -H "Authorization: Bearer dev-token-change-in-production" \
  | jq .

# Generate DKIL keys (see above)
HUMAN_KEY="your-human-key-here"
LOGIC_KEY="calculated-logic-key-here"

# Test deploy endpoint
curl -X POST "http://localhost:8000/api/longevity/deploy" \
  -H "Authorization: Bearer dev-token-change-in-production" \
  -H "Content-Type: application/json" \
  -d "{
    \"run_id\": \"$RUN_ID\",
    \"model_name\": \"ra-longevity-test\",
    \"dkil_signature\": {
      \"human_key\": \"$HUMAN_KEY\",
      \"logic_key\": \"$LOGIC_KEY\",
      \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"
    },
    \"target_registry\": \"staging\"
  }" \
  | jq .
```

## CI/CD Integration

See `.github/workflows/longevity-ci.yml` for the CI/CD pipeline that enforces:

- ✅ Reject model promotion if RA model does not reduce L-Drop by threshold %
- ✅ Only deploy when DKIL dual-signature is validated
- ✅ Automated testing and security scanning

## Security

- **Authentication**: Bearer token required for all endpoints
- **HMAC Signing**: All reports are signed for integrity verification
- **DKIL Validation**: Dual-key requirement prevents unauthorized deployments
- **Environment Variables**: All secrets configured via environment variables
- **No Hardcoded Credentials**: Secure by default

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    RA Longevity Service                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  POST /api/longevity/analyze                                 │
│    ├─ Accept CSV/JSON data                                   │
│    ├─ Encode RA features (RA, D, M, S, LR)                   │
│    ├─ Generate predictions                                   │
│    ├─ Calculate L-Drop metrics                               │
│    └─ Create artifacts (JSON, HTML, DKIL lock)               │
│                                                               │
│  GET /api/longevity/report/:run_id                           │
│    ├─ Check DKIL lock (if exists)                            │
│    └─ Serve JSON or HTML report                              │
│                                                               │
│  POST /api/longevity/deploy                                  │
│    ├─ Validate DKIL dual signature                           │
│    ├─ Create deployment bundle (ZIP)                         │
│    └─ Upload to model registry                               │
│                                                               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │    Artifacts     │
                    │    Directory     │
                    ├──────────────────┤
                    │ - report.json    │
                    │ - report.html    │
                    │ - dkil_lock.json │
                    │ - deployment.json│
                    │ - bundle.zip     │
                    └──────────────────┘
```

## License

See [LICENSE](../../LICENSE).
