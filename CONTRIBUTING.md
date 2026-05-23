# Contributing to WeaveRx

Thank you for helping improve WeaveRx for the medical AI open-source community.

## Development setup

```bash
git clone https://github.com/FratresMedAI/WeaveRx.git
cd WeaveRx
pip install -e ".[dev]"
```

Run the quality checks before opening a pull request:

```bash
ruff check .
mypy src/weaverx
pytest
```

Most tests run offline with `--mock` data. Optional live tests are marked `@pytest.mark.network`.

## Pull request expectations

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

Use the GitHub issue template for bugs and feature requests. Include:

- WeaveRx version (`weaverx --version`)
- Command you ran (redact tokens)
- Expected vs actual behavior

## Code of conduct

Be respectful and constructive. WeaveRx serves researchers, clinicians, and maintainers working under real regulatory and reproducibility constraints.
