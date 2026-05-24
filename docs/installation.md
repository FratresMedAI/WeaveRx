# Installation

WeaveRx is published on [PyPI](https://pypi.org/project/weaverx/) as `weaverx` (lowercase on PyPI; the GitHub repo is titled WeaveRx).

## Requirements

- Python **3.11+** (3.11 and 3.12 tested in CI)

## Recommended: use a virtual environment

Install into an isolated environment so dependencies do not conflict with system Python:

```bash
python -m venv .venv

# Linux / macOS
source .venv/bin/activate

# Windows (PowerShell)
.venv\Scripts\Activate.ps1
```

Then install WeaveRx inside the active environment.

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
python -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\Activate.ps1 on Windows
pip install -e ".[dev]"
pre-commit install
```

Run the offline test suite:

```bash
pytest -m "not network" --cov=weaverx
```

See [Contributing](https://github.com/FratresMedAI/WeaveRx/blob/master/CONTRIBUTING.md) for the full workflow.

## Troubleshooting

**`weaverx: command not found` after install**

- Ensure your virtual environment is activated, or use `python -m weaverx --help`.
- On some systems, add `~/.local/bin` to your `PATH` when installing with `pip install --user`.

**`No matching distribution found for weaverx`**

- Confirm Python 3.11+: `python --version`.
- Upgrade pip: `python -m pip install --upgrade pip`.

**Permission errors during install**

- Prefer a virtual environment instead of `sudo pip install`.
- On managed machines, ask your admin or use `pip install --user weaverx`.

**GitHub install fails**

- Ensure Git is installed and reachable.
- Pin an existing tag (e.g. `@v0.1.2`) rather than a branch name.

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
