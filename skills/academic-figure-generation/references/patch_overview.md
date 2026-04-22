# What `patch_multibackend.py` does

The patch is applied by `scripts/patch_multibackend.py` against a local
PaperBanana checkout. It is **idempotent** — running it twice is safe — and
keeps the original Gemini-only behaviour as the default code path so existing
PaperBanana users can opt in.

## Files modified

### `utils/generation_utils.py`

1. Adds an OpenRouter `AsyncOpenAI` client (`openrouter_client`) that points
   at `https://openrouter.ai/api/v1` with PaperBanana referer headers.
2. Adds a generic OpenAI-compatible client (`copilot_client`) that's
   **disabled by default** and only initialised when the user sets
   `COPILOT_BASE_URL` (or `copilot_base_url` in the yaml). This is the
   escape hatch for users running a local proxy (vLLM, ollama, copilot-api,
   etc.); it is not enabled or auto-probed without explicit configuration.
   Used by `_call_copilot_chat_async`.
3. Adds `call_openrouter_image_chat_with_retry_async()` — same return contract
   as `call_openai_image_generation_with_retry_async()` (a list with one
   base64 PNG), but talks to the OpenRouter chat-completions endpoint with
   `modalities=["image","text"]` and decodes the data URL from
   `message.images[*].image_url.url`.
4. Adds `_call_copilot_chat_async()` that maps a Gemini-style call (a generic
   `contents` list + `google.genai.types.GenerateContentConfig`) onto an
   OpenAI-compatible ChatCompletion. `system_instruction` becomes a system
   message; `candidate_count` becomes N parallel sampled calls.
5. **Front-door routing**: at the top of
   `call_gemini_with_retry_async()`, if `model_name` doesn't match
   `"gemini" in name and "/" not in name`, AND a `copilot_client` was
   initialised, the call is transparently routed to
   `_call_copilot_chat_async()`. If no proxy is configured, the call still
   goes to Google AI direct — the default path stays identical to upstream
   PaperBanana.
6. Adds the quota-aware fallback wrapper around image calls. The wrapper
   catches the trigger conditions documented in `backend_routing.md` and
   retries with the configured fallback model.

### `agents/visualizer_agent.py`

1. Tightens the existing `if "gemini" in self.model_name:` branch to also
   require `"/" not in self.model_name`, so OpenRouter-style ids
   (`google/gemini-...image-preview`) don't accidentally hit the Google AI
   native path.
2. Adds a new `elif` branch for OpenRouter chat-completions image models
   (matches `"/" in name and "image" in name`).

### `agents/vanilla_agent.py`

Same two changes as `visualizer_agent.py`, so the `--exp-mode vanilla` path
also supports the new backends.

### `configs/model_config.yaml`

Adds three commented placeholder fields (without overwriting existing
values):

```yaml
api_keys:
  openrouter_api_key: ""    # or set OPENROUTER_API_KEY env var
  copilot_base_url: ""      # opt-in only; e.g. http://127.0.0.1:4141/v1 for copilot-api,
                            #                  http://127.0.0.1:8000/v1 for vLLM, etc.
  copilot_api_key: ""       # whatever your local proxy expects
```

## What the patch does NOT change

- The Retriever, Planner, Stylist, Critic agents themselves: they all still
  call `generation_utils.call_gemini_with_retry_async(...)`. The routing now
  happens inside that function.
- The image conversion / postprocessing path (`image_utils.convert_png_b64_to_jpg_b64`).
- Existing model defaults in `model_config.yaml` (only adds new optional keys).

## Reverting

If you ever need to roll back, the patch script writes a backup before each
mutation:

```
configs/model_config.yaml.bak.before-multibackend
agents/visualizer_agent.py.bak.before-multibackend
agents/vanilla_agent.py.bak.before-multibackend
utils/generation_utils.py.bak.before-multibackend
```

Move them back to the original names to restore the upstream behaviour.
