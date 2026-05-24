# Installation

WeaveRx is published on [PyPI](https://pypi.org/project/weaverx/) as `weaverx`.

## Requirements

- Python **3.11+** (3.11 and 3.12 tested in CI)

## Install from PyPI

```bash
pip install weaverx
```

Verify:

```bash
weaverx --help
```

## Install from GitHub

Pin a release tag if you need a specific version:

```bash
pip install git+https://github.com/FratresMedAI/WeaveRx.git@v0.1.2
```

## Development install

For local changes or contributions:

```bash
git clone https://github.com/FratresMedAI/WeaveRx.git
cd WeaveRx
pip install -e ".[dev]"
pre-commit install
```

Run the offline test suite:

```bash
pytest -m "not network" --cov=weaverx
```

See [Contributing](https://github.com/FratresMedAI/WeaveRx/blob/master/CONTRIBUTING.md) for the full workflow.

## Configuration

Set API keys and defaults via environment variables — see [Configuration](configuration.md).

Quick mock demo (no keys):

```bash
weaverx triage --repo Project-MONAI/MONAI --issue 42 --mock
```

## GitHub Action

Use a release tag in workflows:

```yaml
- uses: FratresMedAI/WeaveRx@v0.1.2
  with:
    repo: ${{ github.repository }}
    issue_number: ${{ github.event.issue.number }}
    dry_run: "true"
  env:
    XAI_API_KEY: ${{ secrets.XAI_API_KEY }}
```

See [action.yml](https://github.com/FratresMedAI/WeaveRx/blob/master/action.yml) on GitHub.

## Documentation site

Browse the full docs at [fratresmedai.github.io/WeaveRx](https://fratresmedai.github.io/WeaveRx/).
