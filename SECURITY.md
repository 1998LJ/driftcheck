# Security Policy

## Supported Versions

| Version | Supported          |
|---------|-------------------|
| Latest  | ✅ Security updates |
| Older   | ❌ No fixes        |

Only the latest release receives security updates. Keep your driftcheck installation up to date.

## Reporting a Vulnerability

**Public reporting:** Open a GitHub issue with the `security` label. Do NOT include sensitive details (exploits, credentials) in public issues.

**Private reporting:** Use GitHub's private vulnerability reporting:
1. Go to <https://github.com/yunaremaia/driftcheck/security/advisories>
2. Click "Report a security vulnerability"
3. Provide a detailed description, affected version, and reproduction steps

You can also email **yunare@gmail.com** with "driftcheck security" in the subject line for sensitive reports.

## Disclosure Policy

- We aim to address reported vulnerabilities within **30 days**
- A security advisory will be published after a fix is released
- Credit will be given to the reporter (unless requested otherwise)

## Scope

**In scope:**
- Vulnerabilities in the driftcheck detector engine
- Issues allowing arbitrary code execution via detectors or plugins
- Path traversal or file read bugs in scan operations

**Out of scope:**
- Misconfiguration by the user (wrong doc_paths, missing tokens)
- Third-party tools referenced by driftcheck (e.g., upstream package registries)
- Vulnerability scanners that driftcheck integrates with (OSV, etc.)

## Acknowledgments

Thanks to all reporters who help keep driftcheck secure.
