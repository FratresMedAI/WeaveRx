# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.2] - 2026-05-24

### Fixed

- GitHub Action installs from `github.action_path` so external repos can use `FratresMedAI/WeaveRx@v*`
- PyPI release workflow fails visibly when publish breaks (removed `continue-on-error`)

### Changed

- Quickstart leads with `pip install weaverx` and a one-liner demo command
- Code of Conduct enforcement contact points to GitHub issue templates

## [0.1.1] - 2026-05-23

### Added

- PyPI publishing via GitHub Release workflow (trusted publishing)
- GitHub Pages documentation site at [fratresmedai.github.io/WeaveRx](https://fratresmedai.github.io/WeaveRx/)
- Governance files: CODE_OF_CONDUCT, SECURITY, SUPPORT, ETHICS
- Issue and pull request templates
- MkDocs documentation scaffold
- Pre-commit hooks, Dependabot, pip-audit in CI
- pytest coverage gate in CI
- CLI human-review disclaimer on triage output
- Configuration reference in docs
- GitHub Action dry-run screenshot in README

### Changed

- README restructured for scanability (features, quickstart, demo first)
- Repository description and GitHub topics updated
- Badges row moved below title for first-impression polish

## [0.1.0] - 2026-05-23

### Added

- Medical AI issue triage CLI with eight domain categories
- LiteLLM multi-provider support (Grok, Anthropic, OpenAI-compatible)
- Local safeguard heuristics (entropy, repetition, patterns, relevance)
- Auditable `sources` and top-level `status` in JSON output
- GitHub Action for dry-run triage on issues
- Mock mode for offline demos and CI
- Human-in-the-loop defaults (`--dry-run`, `--confirm` for writes)

[Unreleased]: https://github.com/FratresMedAI/WeaveRx/compare/v0.1.2...HEAD
[0.1.2]: https://github.com/FratresMedAI/WeaveRx/releases/tag/v0.1.2
[0.1.1]: https://github.com/FratresMedAI/WeaveRx/releases/tag/v0.1.1
[0.1.0]: https://github.com/FratresMedAI/WeaveRx/releases/tag/v0.1.0
