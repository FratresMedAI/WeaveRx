# LLM providers

| Provider | CLI | API key env | Default model |
| --- | --- | --- | --- |
| Grok | `--llm-provider grok` | `XAI_API_KEY` | `xai/grok-2-latest` |
| Anthropic | `--llm-provider anthropic` | `ANTHROPIC_API_KEY` | `anthropic/claude-3-5-sonnet-20241022` |
| OpenAI-compatible | `--llm-provider openai` | `OPENAI_API_KEY` | `openai/gpt-4o` |

Override model globally: `WEAVERX_LLM_MODEL=anthropic/claude-3-5-haiku-20241022`

Override provider default: `WEAVERX_LLM_PROVIDER=anthropic`

All providers return the same structured JSON schema (`TriageAnalysis` + `sources`).

Copy-paste commands: [llm_provider_examples.md](https://github.com/FratresMedAI/WeaveRx/blob/master/examples/llm_provider_examples.md).

Environment variables: [Configuration](../configuration.md).
