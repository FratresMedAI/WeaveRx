# LLM provider examples

Same triage command shape — swap provider and API key env var.

## Grok (default)

```bash
export XAI_API_KEY=xai-...
weaverx triage --repo Project-MONAI/MONAI --issue 1234 \
  --llm-provider grok --dry-run --json
```

```json
"llm": { "provider": "grok", "model": "xai/grok-2-latest" }
```

## Anthropic

```bash
export ANTHROPIC_API_KEY=sk-ant-...
weaverx triage --repo Project-MONAI/MONAI --issue 1234 \
  --llm-provider anthropic --dry-run --json
```

```json
"llm": { "provider": "anthropic", "model": "anthropic/claude-3-5-sonnet-20241022" }
```

Optional model override:

```bash
export WEAVERX_LLM_MODEL=anthropic/claude-3-5-haiku-20241022
```

## OpenAI-compatible (OpenAI, Azure, vLLM, Ollama gateway, etc.)

```bash
export OPENAI_API_KEY=sk-...
export OPENAI_API_BASE=https://your-host/v1   # omit for api.openai.com
export WEAVERX_LLM_MODEL=openai/gpt-4o        # or your hosted model id

weaverx triage --repo Project-MONAI/MONAI --issue 1234 \
  --llm-provider openai --dry-run --json
```

```json
"llm": { "provider": "openai", "model": "openai/gpt-4o" }
```

## GitHub Action (any provider)

```yaml
env:
  XAI_API_KEY: ${{ secrets.XAI_API_KEY }}
  # ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
  # OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
with:
  llm_provider: anthropic   # grok | anthropic | openai
```
