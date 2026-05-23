# Documentation setup

Local preview:

```bash
pip install -e ".[docs]"
mkdocs serve
```

Open http://127.0.0.1:8000

Build (strict):

```bash
mkdocs build --strict
```

Screenshots are generated separately:

```bash
pip install -e ".[dev]"
pip install playwright
playwright install chromium
python scripts/generate_doc_screenshots.py
```

See [screenshots/README.md](screenshots/README.md) for asset details.
