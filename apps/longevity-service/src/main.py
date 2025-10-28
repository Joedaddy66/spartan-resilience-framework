"""
RA Longevity MLOps Microservice API.

Provides endpoints for:
- Analyzing RA longevity models (tabular/time-series)
- Retrieving analysis reports with DKIL validation
- Deploying models to registry with dual-signature validation
"""
import os
import json
import uuid
import hmac
import hashlib
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from io import BytesIO, StringIO

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Header, Body, Request
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import pandas as pd
import numpy as np
import uvicorn

# Initialize FastAPI app
app = FastAPI(
    title="RA Longevity MLOps API",
    description="Microservice for RA longevity model analysis, reporting, and deployment",
    version="1.0.0"
)

# Configuration
ARTIFACTS_DIR = Path(os.getenv("ARTIFACTS_DIR", "/home/runner/work/spartan-resilience-framework/spartan-resilience-framework/artifacts"))
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

# Serve artifacts as static files
app.mount("/artifacts", StaticFiles(directory=str(ARTIFACTS_DIR)), name="artifacts")

# Security configuration
BEARER_TOKEN = os.getenv("BEARER_TOKEN", "dev-token-change-in-production")
HMAC_SECRET = os.getenv("SAVE_HMAC_SECRET")
if not HMAC_SECRET:
    raise ValueError(
        "SAVE_HMAC_SECRET environment variable must be set. "
        "Generate a strong secret with: python -c 'import secrets; print(secrets.token_hex(32))'"
    )

# L-Drop threshold for model promotion (percentage)
LDROP_THRESHOLD = float(os.getenv("LDROP_THRESHOLD", "5.0"))


# ============================================================================
# Pydantic Models
# ============================================================================

class AnalyzeRequest(BaseModel):
    """Request model for longevity analysis."""
    mode: str = Field(..., description="Analysis mode: 'tabular' or 'time_series'")
    data: Optional[List[Dict[str, Any]]] = Field(None, description="JSON tabular data (if not using CSV upload)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "mode": "tabular",
                "data": [
                    {"RA": 0.85, "D": 2.1, "M": 1.5, "S": 3.2, "LR": 0.001},
                    {"RA": 0.92, "D": 1.8, "M": 1.3, "S": 2.9, "LR": 0.0005}
                ]
            }
        }


class AnalyzeResponse(BaseModel):
    """Response model for longevity analysis."""
    run_id: str = Field(..., description="Unique run identifier")
    predictions: List[Dict[str, Any]] = Field(..., description="Model predictions")
    ldrop_metrics: Dict[str, float] = Field(..., description="L-Drop metrics")
    ra_score_deltas: List[float] = Field(..., description="RA score changes")
    report_url: str = Field(..., description="URL to view full report")
    artifacts_created: List[str] = Field(..., description="List of artifact files created")


class DKILSignature(BaseModel):
    """Dual-Key Integrity Lock signature."""
    human_key: str = Field(..., description="Human reviewer signature/key")
    logic_key: str = Field(..., description="Automated logic validation key")
    timestamp: str = Field(..., description="Signature timestamp")


class DeployRequest(BaseModel):
    """Request model for model deployment."""
    run_id: str = Field(..., description="Run ID to deploy")
    model_name: str = Field(..., description="Name for deployed model")
    dkil_signature: DKILSignature = Field(..., description="DKIL dual signature")
    target_registry: str = Field(default="default", description="Target model registry")
    
    class Config:
        json_schema_extra = {
            "example": {
                "run_id": "run_abc123",
                "model_name": "ra-longevity-v1",
                "dkil_signature": {
                    "human_key": "human_reviewer_signature_hash",
                    "logic_key": "automated_logic_validation_hash",
                    "timestamp": "2025-10-28T18:00:00Z"
                },
                "target_registry": "production"
            }
        }


class DeployResponse(BaseModel):
    """Response model for deployment."""
    success: bool
    model_id: str
    registry_url: str
    bundle_path: str


# ============================================================================
# Authentication
# ============================================================================

def verify_bearer_token(authorization: Optional[str] = Header(None)) -> bool:
    """Verify bearer token authentication."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization format")
    
    token = authorization.replace("Bearer ", "")
    if token != BEARER_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid bearer token")
    
    return True


# ============================================================================
# Helper Functions
# ============================================================================

def generate_run_id() -> str:
    """Generate unique run identifier."""
    return f"run_{uuid.uuid4().hex[:12]}"


def calculate_hmac_signature(data: Dict[str, Any]) -> str:
    """Calculate HMAC signature for data integrity."""
    data_json = json.dumps(data, sort_keys=True)
    signature = hmac.new(
        HMAC_SECRET.encode(),
        data_json.encode(),
        hashlib.sha256
    ).hexdigest()
    return signature


def encode_ra_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Encode RA features (RA, D, M, S, LR).
    
    Args:
        df: DataFrame with raw features
        
    Returns:
        DataFrame with encoded features
    """
    # Simple feature encoding - in production this would use trained encoders
    encoded = df.copy()
    
    # Normalize RA score (0-1)
    if 'RA' in encoded.columns:
        encoded['RA_normalized'] = encoded['RA'].clip(0, 1)
    
    # Log transform for D, M, S
    for col in ['D', 'M', 'S']:
        if col in encoded.columns:
            encoded[f'{col}_log'] = encoded[col].apply(lambda x: np.log1p(max(x, 0)))
    
    # Scale LR
    if 'LR' in encoded.columns:
        encoded['LR_scaled'] = encoded['LR'] * 1000
    
    return encoded


def calculate_ldrop_metrics(predictions: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Calculate L-Drop (longevity drop) metrics.
    
    Args:
        predictions: List of prediction dictionaries
        
    Returns:
        Dictionary with L-Drop metrics
    """
    if not predictions:
        return {"ldrop_mean": 0.0, "ldrop_reduction_pct": 0.0}
    
    # Extract predicted longevity values
    longevities = [p.get('predicted_longevity', 0) for p in predictions]
    
    if not longevities:
        return {"ldrop_mean": 0.0, "ldrop_reduction_pct": 0.0}
    
    # Calculate drops
    drops = []
    for i in range(len(longevities) - 1):
        drop = max(0, longevities[i] - longevities[i + 1])
        drops.append(drop)
    
    ldrop_mean = sum(drops) / len(drops) if drops else 0.0
    
    # Calculate reduction percentage (compared to baseline of 10%)
    baseline_ldrop = 0.10
    ldrop_reduction_pct = ((baseline_ldrop - ldrop_mean) / baseline_ldrop) * 100 if baseline_ldrop > 0 else 0.0
    
    return {
        "ldrop_mean": round(ldrop_mean, 4),
        "ldrop_reduction_pct": round(ldrop_reduction_pct, 2),
        "ldrop_max": round(max(drops) if drops else 0.0, 4),
        "ldrop_min": round(min(drops) if drops else 0.0, 4),
    }


def generate_predictions(encoded_df: pd.DataFrame, mode: str) -> List[Dict[str, Any]]:
    """
    Generate model predictions.
    
    Args:
        encoded_df: Encoded feature DataFrame
        mode: Analysis mode ('tabular' or 'time_series')
        
    Returns:
        List of prediction dictionaries
    """
    predictions = []
    
    for idx, row in encoded_df.iterrows():
        # Simple prediction model - in production this would use trained ML model
        ra_score = row.get('RA', 0.5)
        d_value = row.get('D', 1.0)
        m_value = row.get('M', 1.0)
        s_value = row.get('S', 1.0)
        lr_value = row.get('LR', 0.001)
        
        # Calculate predicted longevity (simplified formula)
        predicted_longevity = ra_score * (1.0 / (1.0 + d_value)) * m_value * (1.0 + s_value) * (1.0 - lr_value * 100)
        
        prediction = {
            "index": int(idx),
            "ra_score": round(ra_score, 4),
            "predicted_longevity": round(predicted_longevity, 4),
            "confidence": round(0.85 + (ra_score * 0.1), 4),  # Simplified confidence
            "features": {
                "RA": ra_score,
                "D": d_value,
                "M": m_value,
                "S": s_value,
                "LR": lr_value
            }
        }
        predictions.append(prediction)
    
    return predictions


def create_report_artifacts(run_id: str, data: Dict[str, Any]) -> List[str]:
    """
    Create report artifacts (JSON, HTML, DKIL lock file).
    
    Args:
        run_id: Run identifier
        data: Report data
        
    Returns:
        List of created artifact file paths
    """
    run_dir = ARTIFACTS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    
    artifacts = []
    
    # 1. Save JSON payload
    json_path = run_dir / "report.json"
    with open(json_path, 'w') as f:
        json.dump(data, f, indent=2)
    artifacts.append(str(json_path.relative_to(ARTIFACTS_DIR)))
    
    # 2. Generate HTML report
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>RA Longevity Analysis Report - {run_id}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
        .container {{ background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 3px solid #4CAF50; padding-bottom: 10px; }}
        h2 {{ color: #555; margin-top: 30px; }}
        .metric {{ background: #e8f5e9; padding: 15px; margin: 10px 0; border-radius: 4px; }}
        .metric-label {{ font-weight: bold; color: #2e7d32; }}
        .metric-value {{ font-size: 24px; color: #1b5e20; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th {{ background: #4CAF50; color: white; padding: 12px; text-align: left; }}
        td {{ padding: 10px; border-bottom: 1px solid #ddd; }}
        tr:hover {{ background: #f5f5f5; }}
        .status {{ padding: 5px 10px; border-radius: 3px; font-weight: bold; }}
        .status-pass {{ background: #c8e6c9; color: #2e7d32; }}
        .status-warning {{ background: #fff9c4; color: #f57f17; }}
        .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>RA Longevity Analysis Report</h1>
        <p><strong>Run ID:</strong> {run_id}</p>
        <p><strong>Timestamp:</strong> {data.get('timestamp', 'N/A')}</p>
        <p><strong>Mode:</strong> {data.get('mode', 'N/A')}</p>
        
        <h2>L-Drop Metrics</h2>
        <div class="metric">
            <div class="metric-label">Mean L-Drop</div>
            <div class="metric-value">{data.get('ldrop_metrics', {}).get('ldrop_mean', 0):.4f}</div>
        </div>
        <div class="metric">
            <div class="metric-label">L-Drop Reduction</div>
            <div class="metric-value">{data.get('ldrop_metrics', {}).get('ldrop_reduction_pct', 0):.2f}%</div>
            <span class="status {'status-pass' if data.get('ldrop_metrics', {}).get('ldrop_reduction_pct', 0) >= LDROP_THRESHOLD else 'status-warning'}">
                {'PASS' if data.get('ldrop_metrics', {}).get('ldrop_reduction_pct', 0) >= LDROP_THRESHOLD else 'BELOW THRESHOLD'}
            </span>
        </div>
        
        <h2>Predictions</h2>
        <table>
            <thead>
                <tr>
                    <th>Index</th>
                    <th>RA Score</th>
                    <th>Predicted Longevity</th>
                    <th>Confidence</th>
                </tr>
            </thead>
            <tbody>
"""
    
    for pred in data.get('predictions', [])[:10]:  # Show first 10
        html_content += f"""
                <tr>
                    <td>{pred.get('index', 'N/A')}</td>
                    <td>{pred.get('ra_score', 0):.4f}</td>
                    <td>{pred.get('predicted_longevity', 0):.4f}</td>
                    <td>{pred.get('confidence', 0):.4f}</td>
                </tr>
"""
    
    html_content += f"""
            </tbody>
        </table>
        
        <div class="footer">
            <p>Generated by RA Longevity MLOps Service</p>
            <p>Report Signature: {data.get('signature', 'N/A')}</p>
        </div>
    </div>
</body>
</html>
"""
    
    html_path = run_dir / "report.html"
    with open(html_path, 'w') as f:
        f.write(html_content)
    artifacts.append(str(html_path.relative_to(ARTIFACTS_DIR)))
    
    # 3. Create DKIL lock file if threshold met
    ldrop_reduction = data.get('ldrop_metrics', {}).get('ldrop_reduction_pct', 0)
    if ldrop_reduction >= LDROP_THRESHOLD:
        dkil_data = {
            "run_id": run_id,
            "timestamp": data.get('timestamp'),
            "ldrop_reduction_pct": ldrop_reduction,
            "threshold_met": True,
            "requires_dual_signature": True,
            "human_key_required": True,
            "logic_key_required": True,
        }
        dkil_path = run_dir / "dkil_lock.json"
        with open(dkil_path, 'w') as f:
            json.dump(dkil_data, f, indent=2)
        artifacts.append(str(dkil_path.relative_to(ARTIFACTS_DIR)))
    
    return artifacts


def validate_dkil_signature(run_id: str, signature: DKILSignature) -> bool:
    """
    Validate DKIL dual signature.
    
    Args:
        run_id: Run identifier
        signature: DKIL signature to validate
        
    Returns:
        True if signature is valid
    """
    # Check if DKIL lock file exists
    lock_path = ARTIFACTS_DIR / run_id / "dkil_lock.json"
    if not lock_path.exists():
        raise HTTPException(status_code=404, detail="DKIL lock file not found - threshold may not have been met")
    
    with open(lock_path, 'r') as f:
        lock_data = json.load(f)
    
    # Validate human key (in production, this would verify against a database/registry)
    if not signature.human_key or len(signature.human_key) < 32:
        raise HTTPException(status_code=400, detail="Invalid human key signature")
    
    # Validate logic key (verify it's a valid HMAC of the lock data)
    expected_logic_key = calculate_hmac_signature(lock_data)
    if not hmac.compare_digest(signature.logic_key, expected_logic_key):
        raise HTTPException(status_code=400, detail="Invalid logic key signature")
    
    return True


def create_deployment_bundle(run_id: str, model_name: str) -> str:
    """
    Create deployment bundle (ZIP) with all artifacts.
    
    Args:
        run_id: Run identifier
        model_name: Model name
        
    Returns:
        Path to created bundle
    """
    run_dir = ARTIFACTS_DIR / run_id
    bundle_path = ARTIFACTS_DIR / f"{model_name}_{run_id}_bundle.zip"
    
    with zipfile.ZipFile(bundle_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in run_dir.glob("*"):
            if file_path.is_file():
                zipf.write(file_path, arcname=file_path.name)
    
    return str(bundle_path.relative_to(ARTIFACTS_DIR))


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "service": "RA Longevity MLOps API",
        "version": "1.0.0",
        "endpoints": {
            "analyze": "POST /api/longevity/analyze",
            "report": "GET /api/longevity/report/{run_id}",
            "deploy": "POST /api/longevity/deploy"
        },
        "documentation": "/docs"
    }


@app.get("/health", tags=["Health"])
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(datetime.UTC).isoformat() if hasattr(datetime, 'UTC') else datetime.utcnow().isoformat(),
        "artifacts_dir": str(ARTIFACTS_DIR),
        "artifacts_accessible": ARTIFACTS_DIR.exists()
    }


@app.post("/api/longevity/analyze", response_model=AnalyzeResponse, tags=["Analysis"])
async def analyze(
    request: Request,
    authenticated: bool = Depends(verify_bearer_token)
):
    """
    Analyze RA longevity model.
    
    Accepts either CSV upload or JSON tabular data.
    Performs RA feature encoding and returns predictions with L-Drop metrics.
    """
    # Determine content type and parse accordingly
    content_type = request.headers.get("content-type", "")
    
    if "application/json" in content_type:
        # Handle JSON request
        body = await request.json()
        mode = body.get("mode")
        data = body.get("data")
        file = None
    elif "multipart/form-data" in content_type:
        # Handle form data with file upload
        form = await request.form()
        mode = form.get("mode")
        data = None
        file = form.get("file")
    else:
        raise HTTPException(status_code=400, detail="Invalid content type")
    
    # Validate mode
    if not mode or mode not in ["tabular", "time_series"]:
        raise HTTPException(status_code=400, detail="Mode must be 'tabular' or 'time_series'")
    
    # Load data from CSV or JSON
    if file:
        content = await file.read()
        df = pd.read_csv(BytesIO(content))
    elif data:
        df = pd.DataFrame(data)
    else:
        raise HTTPException(status_code=400, detail="Either 'file' or 'data' must be provided")
    
    # Validate required columns
    required_cols = ['RA', 'D', 'M', 'S', 'LR']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required columns: {missing_cols}. Required: {required_cols}"
        )
    
    # Generate run ID
    run_id = generate_run_id()
    
    # Encode features
    encoded_df = encode_ra_features(df)
    
    # Generate predictions
    predictions = generate_predictions(encoded_df, mode)
    
    # Calculate L-Drop metrics
    ldrop_metrics = calculate_ldrop_metrics(predictions)
    
    # Calculate RA score deltas
    ra_scores = [p['ra_score'] for p in predictions]
    ra_score_deltas = [ra_scores[i+1] - ra_scores[i] for i in range(len(ra_scores) - 1)]
    
    # Create report data
    report_data = {
        "run_id": run_id,
        "timestamp": datetime.now(datetime.UTC).isoformat() if hasattr(datetime, 'UTC') else datetime.utcnow().isoformat(),
        "mode": mode,
        "predictions": predictions,
        "ldrop_metrics": ldrop_metrics,
        "ra_score_deltas": ra_score_deltas,
        "input_shape": list(df.shape),
    }
    
    # Add signature
    report_data["signature"] = calculate_hmac_signature(report_data)
    
    # Create artifacts
    artifacts_created = create_report_artifacts(run_id, report_data)
    
    return AnalyzeResponse(
        run_id=run_id,
        predictions=predictions,
        ldrop_metrics=ldrop_metrics,
        ra_score_deltas=ra_score_deltas,
        report_url=f"/api/longevity/report/{run_id}",
        artifacts_created=artifacts_created
    )


@app.get("/api/longevity/report/{run_id}", tags=["Reports"])
async def get_report(
    run_id: str,
    format: str = "json",
    authenticated: bool = Depends(verify_bearer_token)
):
    """
    Get analysis report by run ID.
    
    Returns JSON or HTML report. Checks DKIL lock file if enabled.
    """
    run_dir = ARTIFACTS_DIR / run_id
    
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail=f"Report for run_id '{run_id}' not found")
    
    # Check if DKIL is required
    dkil_path = run_dir / "dkil_lock.json"
    if dkil_path.exists():
        # DKIL check is informational - in production, might enforce restrictions
        with open(dkil_path, 'r') as f:
            dkil_data = json.load(f)
    
    if format.lower() == "html":
        html_path = run_dir / "report.html"
        if not html_path.exists():
            raise HTTPException(status_code=404, detail="HTML report not found")
        return FileResponse(html_path, media_type="text/html")
    
    else:  # JSON format
        json_path = run_dir / "report.json"
        if not json_path.exists():
            raise HTTPException(status_code=404, detail="JSON report not found")
        
        with open(json_path, 'r') as f:
            report_data = json.load(f)
        
        return JSONResponse(content=report_data)


@app.post("/api/longevity/deploy", response_model=DeployResponse, tags=["Deployment"])
async def deploy_model(
    request: DeployRequest,
    authenticated: bool = Depends(verify_bearer_token)
):
    """
    Deploy model to registry.
    
    Validates DKIL dual signature and uploads model to model registry.
    Requires both human and logic keys in the request.
    """
    run_id = request.run_id
    
    # Validate run exists
    run_dir = ARTIFACTS_DIR / run_id
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")
    
    # Validate DKIL signature
    validate_dkil_signature(run_id, request.dkil_signature)
    
    # Create deployment bundle
    bundle_path = create_deployment_bundle(run_id, request.model_name)
    
    # In production, upload to actual model registry (MLflow, Vertex AI, etc.)
    model_id = f"model_{uuid.uuid4().hex[:8]}"
    registry_url = f"registry://{request.target_registry}/{request.model_name}/{model_id}"
    
    # Log deployment event
    deployment_event = {
        "timestamp": datetime.now(datetime.UTC).isoformat() if hasattr(datetime, 'UTC') else datetime.utcnow().isoformat(),
        "run_id": run_id,
        "model_name": request.model_name,
        "model_id": model_id,
        "registry_url": registry_url,
        "dkil_validated": True,
        "human_key": request.dkil_signature.human_key[:16] + "...",  # Partial key for logging
        "signature_timestamp": request.dkil_signature.timestamp,
    }
    deployment_path = run_dir / "deployment.json"
    with open(deployment_path, 'w') as f:
        json.dump(deployment_event, f, indent=2)
    
    return DeployResponse(
        success=True,
        model_id=model_id,
        registry_url=registry_url,
        bundle_path=bundle_path
    )


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
