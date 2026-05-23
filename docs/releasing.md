# Releasing WeaveRx

This project uses semantic version tags and GitHub Releases. PyPI publish is planned but not automated yet.

## Cut a release

1. Update [CHANGELOG.md](https://github.com/FratresMedAI/WeaveRx/blob/master/CHANGELOG.md) — move `[Unreleased]` items into a new version section.
2. Bump `version` in [pyproject.toml](https://github.com/FratresMedAI/WeaveRx/blob/master/pyproject.toml) if needed.
3. Commit and push to `master`.
4. Create and push a tag:

```bash
git tag -a v0.1.1 -m "v0.1.1"
git push origin v0.1.1
```

The [release workflow](https://github.com/FratresMedAI/WeaveRx/blob/master/.github/workflows/release.yml) runs on `v*` tags:

- ruff, mypy, pytest with coverage
- builds sdist + wheel
- attaches artifacts to the GitHub Release

## Verify locally before tagging

```bash
pip install -e ".[dev]"
ruff check .
mypy src/weaverx
pytest --cov=weaverx --cov-fail-under=75
python -m build
```

## Future PyPI publish (manual checklist)

When ready to publish to PyPI:

1. Create a PyPI project and configure [trusted publishing](https://docs.pypi.org/trusted-publishers/) or store `PYPI_API_TOKEN` as a repository secret.
2. Add a publish step to `release.yml` (e.g. `pypa/gh-action-pypi-publish`).
3. Update README install instructions to `pip install weaverx`.
4. Add a PyPI badge to the README badge row.

Until then, install from GitHub:

```bash
pip install git+https://github.com/FratresMedAI/WeaveRx.git@v0.1.0
```
