# Security Policy

## Supported Versions

We release patches and security fixes for the current minor release series.

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |
| < 0.1.0 | :x:                |

## Reporting a Vulnerability

The driftcheck team takes security issues seriously. If you discover a security vulnerability, please do **not** open a public issue.

### Preferred Method: GitHub Private Vulnerability Reporting
You can report vulnerabilities directly through GitHub's Security Advisories tab:
1. Navigate to the repository's **Security** tab.
2. Click **Report a vulnerability**.
3. Fill in the details including affected versions, reproduction steps, and potential impact.

### Alternative Method: Email
If you prefer not to use GitHub advisories, please email the maintainer directly at:
- **Email:** `yunare@gmail.com`
- **Subject:** `[SECURITY] Vulnerability report in driftcheck`

Please include:
- A detailed description of the vulnerability.
- Steps to reproduce or proof-of-concept code.
- Potential impact and suggested mitigations (if available).

## Disclosure Policy

- **Initial Response:** We will acknowledge receipt of your vulnerability report within 48 hours.
- **Assessment & Fix:** We will assess the vulnerability, keep you informed of progress, and prepare a patch.
- **Public Disclosure:** Once a fix is released, we will coordinate public disclosure and provide attribution to the reporter (unless anonymity is requested).

## Scope

### In Scope
- Vulnerabilities in `driftcheck` core logic, detectors, and CLI parsing that could lead to arbitrary code execution, unintended file access, or Denial of Service during repository analysis.
- Supply-chain risks in package release and distribution workflows.

### Out of Scope
- Reports from automated scanners without a demonstrable proof-of-concept.
- Social engineering or phishing targeting maintainers.
