# LeonideX RSA Audit GitHub Action

Composite GitHub Action that performs RSA key auditing via the LeonideX service.

## Description

This action posts RSA public key information to a LeonideX audit endpoint and retrieves a sanitized audit result. The action only displays public-safe information:
- **Decision**: PASS or FAIL
- **Depth Information**: "Depth ≥ threshold" (no raw metrics)

No formulas, dataset rows, or internal metrics are exposed.

## Inputs

### `pubkey_path`
**Required**: No  
**Default**: `keys/sample.pub`  
**Description**: Path to the RSA public key file to audit.

### `leonidex_endpoint`
**Required**: Yes  
**Description**: URL of the LeonideX audit service endpoint.

### `leonidex_token`
**Required**: Yes  
**Description**: Authentication token for the LeonideX service (Bearer token).

## Outputs

### `decision`
The audit decision: `PASS` or `FAIL`.

### `report_path`
Path to the generated `report.json` file.

## Example Usage

```yaml
- name: Run RSA Audit
  uses: ./github-action
  with:
    pubkey_path: keys/my-key.pub
    leonidex_endpoint: ${{ secrets.LEONIDEX_ENDPOINT }}
    leonidex_token: ${{ secrets.LEONIDEX_TOKEN }}
```

## Complete Workflow Example

See `.github/workflows/leonidex_audit.yml` for a complete workflow that:
1. Checks out the repository
2. Runs the audit action
3. Uploads the report as an artifact

## Report Format

The action generates a `report.json` file with the following structure:

```json
{
  "schema": "leonidex-audit-v1",
  "decision": "PASS",
  "depth_floor_shown": "Depth ≥ threshold",
  "fingerprint": "73e4386914986020",
  "report_hash": "ae0b8321be728b080a0014cf2affadb2779d461aaf2f42d7c91841fabe95c63b",
  "signature": "simulated_signature_73e43869",
  "timestamp": "2025-11-02T17:52:23.215941+00:00",
  "pubkey_path": "keys/sample.pub"
}
```

## Requirements

- Python 3.x (for JSON parsing)
- curl (for HTTP requests)
- Standard Unix utilities (date, sed, grep, cut)

These are typically available in all GitHub Actions runners.
