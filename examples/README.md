# WeaveRx examples

Sample outputs for documentation, tests, and offline demos.

| Path | Description |
|------|-------------|
| [`../docs/screenshots/`](../docs/screenshots/) | README terminal screenshots (PNG) |
| [`captures/triage-clean.txt`](captures/triage-clean.txt) | Text fallback — clean mock triage |
| [`captures/safeguard-warning.txt`](captures/safeguard-warning.txt) | Text fallback — high-risk safeguard |
| [`sample_triage_output.json`](sample_triage_output.json) | Full JSON triage result |
| [`sample_safeguard_warning.json`](sample_safeguard_warning.json) | Safeguard block when heuristics fire |
| [`llm_provider_examples.md`](llm_provider_examples.md) | Grok / Anthropic / OpenAI copy-paste commands |
| [`mock_issue.md`](mock_issue.md) | Mock GitHub issue used in `--mock` mode |

Regenerate screenshots and text captures:

```bash
pip install -e ".[dev]"
pip install playwright cairosvg   # playwright on Windows; cairosvg on Linux
playwright install chromium       # if using playwright
python scripts/generate_doc_screenshots.py
```
