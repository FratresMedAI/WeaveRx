# Contributing to WeaveRx

Thank you for helping improve WeaveRx for the medical AI open-source community.

## Community standards

- Read and follow our [Code of Conduct](CODE_OF_CONDUCT.md).
- Review [ETHICS.md](ETHICS.md) for responsible-use constraints in this domain.
- Report security issues privately via [SECURITY.md](SECURITY.md) — never in public issues.

## Development setup

```bash
git clone https://github.com/FratresMedAI/WeaveRx.git
cd WeaveRx
pip install -e ".[dev]"
pre-commit install   # optional but recommended
```

Run the quality checks before opening a pull request:

```bash
pre-commit run --all-files   # or: ruff check .
mypy src/weaverx
pytest --cov=weaverx
```

Most tests run offline with `--mock` data. Optional live tests are marked `@pytest.mark.network` — run them explicitly with `pytest -m network`.

## Pull request expectations

Use the [pull request template](.github/PULL_REQUEST_TEMPLATE.md). In summary:

- Keep changes focused and explain the **why** in the PR description.
- Match existing code style (type hints, ruff/mypy clean).
- Add or update tests for behavior changes.
- Do not weaken safety defaults (dry-run, confirmation gates, advisory safeguards).

## Safety constraints

WeaveRx is **human-in-the-loop** tooling:

- Never auto-post triage comments without explicit `--post-comment` and `--confirm`.
- Safeguard checks are advisory — they warn, they do not block.
- Do not add features that encourage sharing PHI or patient identifiers in GitHub issues.

## Reporting issues

Use the GitHub issue templates:

- [Bug report](.github/ISSUE_TEMPLATE/bug_report.yml)
- [Feature request](.github/ISSUE_TEMPLATE/feature_request.yml)
- [WeaveRx feedback](.github/ISSUE_TEMPLATE/triage_feedback.yml)

Include WeaveRx version (`weaverx --version`), the command you ran (redact tokens), and expected vs actual behavior.

See [SUPPORT.md](SUPPORT.md) for response expectations.

## Releases

Maintainers: see [docs/releasing.md](docs/releasing.md) for tagging and GitHub Release workflow.
