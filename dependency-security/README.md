# Dependency Security Scanning

This directory contains automated dependency security scanning tools compliant with SIG 3.3.9 (Dependency Strength).

## scan.sh

Automated script that scans dependencies for vulnerabilities and outdated packages.

### Tools Used

- **pip**: Checks for outdated Python packages
- **OWASP Dependency-Check**: Scans for known vulnerabilities in Python and Node.js dependencies
- **Trivy**: Scans container images for vulnerabilities

### Enforcement Policies

The script implements native tool-level blocking for security compliance:

#### Backend (Python) - OWASP Dependency-Check
- **Blocking Policy**: `--failOnCVSS 9.0`
- **Behavior**: Fails immediately if any vulnerability with CVSS score >= 9.0 (CRITICAL) is detected
- **Scope**: Backend Python dependencies only

#### Backend Container - Trivy
- **Blocking Policy**: `--exit-code 1 --severity CRITICAL`
- **Behavior**: Fails immediately if any CRITICAL severity vulnerability is detected
- **Scope**: Backend container image only

#### Frontend (React) - OWASP Dependency-Check
- **Policy**: Report only (no blocking)
- **Behavior**: Generates reports but does not fail the pipeline
- **Scope**: Frontend Node.js dependencies

#### Frontend Container - Trivy
- **Policy**: Report only (no blocking)
- **Behavior**: Generates reports but does not fail the pipeline
- **Scope**: Frontend container image

### Environment Variables

#### NVD_API_KEY (Optional)
The script accepts an NVD API key for faster OWASP Dependency-Check scans. The NVD API has rate limits, and using an API key provides higher rate limits.

**How to use:**
```bash
export NVD_API_KEY="your-api-key-here"
./dependency-security/scan.sh
```

**Get a free API key:** https://nvd.nist.gov/developers/request-an-api-key

### Running the Scan

```bash
cd dependency-security
./scan.sh
```

### Reports

After execution, reports are generated in a timestamped directory under `reports/`:

- `reports/<timestamp>/pip/outdated-base.txt` - Outdated base Python packages
- `reports/<timestamp>/pip/outdated-dev.txt` - Outdated dev Python packages
- `reports/<timestamp>/dependency-check/backend/dependency-check-report.html` - Backend vulnerability report (HTML)
- `reports/<timestamp>/dependency-check/backend/dependency-check-report.json` - Backend vulnerability report (JSON)
- `reports/<timestamp>/dependency-check/frontend/dependency-check-report.html` - Frontend vulnerability report (HTML)
- `reports/<timestamp>/dependency-check/frontend/dependency-check-report.json` - Frontend vulnerability report (JSON)
- `reports/<timestamp>/trivy/backend.json` - Backend container image vulnerabilities
- `reports/<timestamp>/trivy/frontend.json` - Frontend container image vulnerabilities
- `reports/<timestamp>/summary.txt` - Executive summary of all scans

### Security Notes

**NO API KEKS ARE HARDCODED** in this script. The NVD API key must be provided via environment variable. This follows security best practices to prevent credential exposure in version control.

If no NVD API key is provided, the scan will still work but may be slower due to NVD API rate limits.
