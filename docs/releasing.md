# Releasing WeaveRx

Semantic version tags trigger the [release workflow](https://github.com/FratresMedAI/WeaveRx/blob/master/.github/workflows/release.yml), which:

1. Runs ruff, mypy, and pytest with coverage
2. Builds sdist + wheel
3. Publishes to PyPI (trusted publishing)
4. Creates a GitHub Release with artifacts attached

Live docs deploy automatically on push to `master` via the [docs workflow](https://github.com/FratresMedAI/WeaveRx/blob/master/.github/workflows/docs.yml) to [fratresmedai.github.io/WeaveRx](https://fratresmedai.github.io/WeaveRx/).

## One-time PyPI trusted publishing setup

Before the first `v*` tag publish succeeds on PyPI:

1. Create the `weaverx` project on [pypi.org](https://pypi.org/) (or claim the name if reserved).
2. Add a [trusted publisher](https://docs.pypi.org/trusted-publishers/):
   - **PyPI publisher name:** `pypi`
   - **Repository:** `FratresMedAI/WeaveRx`
   - **Workflow:** `release.yml`
   - **Environment name:** (leave blank)
3. Push a tag — no `PYPI_API_TOKEN` secret required.

## Cut a release

1. Update [CHANGELOG.md](https://github.com/FratresMedAI/WeaveRx/blob/master/CHANGELOG.md).
2. Bump `version` in [pyproject.toml](https://github.com/FratresMedAI/WeaveRx/blob/master/pyproject.toml) and `src/weaverx/__init__.py`.
3. Commit and push to `master`.
4. Tag and push:

```bash
git tag -a v0.1.1 -m "v0.1.1"
git push origin v0.1.1
```

## Verify locally before tagging

```bash
pip install -e ".[dev]"
ruff check .
mypy src/weaverx
pytest --cov=weaverx --cov-fail-under=75
python -m build
mkdocs build --strict
```

## Install after release

```bash
pip install weaverx
```

Fallback:

```bash
pip install git+https://github.com/FratresMedAI/WeaveRx.git@v0.1.1
```
