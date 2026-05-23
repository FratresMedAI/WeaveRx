# WeaveRx README screenshots

Terminal captures for the [README on GitHub](https://github.com/FratresMedAI/WeaveRx/blob/master/README.md) **See it in action** section.

## Files

| File | Shows |
|------|--------|
| `triage-clean.png` | Mock triage with clean safeguard and draft panel |
| `safeguard-warning.png` | High-risk safeguard flags and red draft panel border |
| `github-action-dry-run.png` | GitHub Actions-style dry-run log for README |

## Regenerate

```bash
pip install -e ".[dev]"
pip install cairosvg              # Linux/macOS
pip install playwright            # Windows fallback
playwright install chromium       # if using playwright
python scripts/generate_doc_screenshots.py
```

The script uses the same Rich renderer as the CLI (`render_triage_result`) at **100 columns** on a **dark terminal theme** (Rich `MONOKAI`). The safeguard screenshot uses a synthetic draft that triggers local heuristics — no new CLI flags.

Text fallbacks (accessibility): [examples/captures/](https://github.com/FratresMedAI/WeaveRx/tree/master/examples/captures).
