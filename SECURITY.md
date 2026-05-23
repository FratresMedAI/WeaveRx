# Security Policy

## Supported versions

| Version | Supported |
| ------- | --------- |
| 0.1.x   | Yes       |
| < 0.1   | No        |

Security fixes are applied to the latest release on the `master` branch.

## Reporting a vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

Please report security issues privately using [GitHub Security Advisories](https://github.com/FratresMedAI/WeaveRx/security/advisories/new) or by emailing the maintainers (see repository contact).

Include:

- A description of the issue and potential impact
- Steps to reproduce
- Affected version(s)
- Any suggested fix or mitigation

We aim to acknowledge reports within **5 business days** and provide a timeline for a fix when possible.

## What not to include

- Patient health information (PHI), identifiers, or clinical data
- Live API keys, tokens, or credentials (use redacted placeholders)
- Private repository contents you are not authorized to share

## Safe disclosure

We follow coordinated disclosure. Please allow reasonable time for a patch before public disclosure. We credit reporters in release notes when they wish to be named.

## Scope

This policy covers the WeaveRx CLI, GitHub Action, and repository code. It does **not** cover third-party services (GitHub, LLM providers, or your own deployment secrets).

For general bugs and feature requests, use the [bug report](.github/ISSUE_TEMPLATE/bug_report.yml) template instead.
