# Backend Routing & Quota Fallback

## Image backends supported

| Backend id | Endpoint | Notes |
|------------|----------|-------|
| `gemini-3-pro-image-preview` | Google AI native (`google.genai`) | NanoBanana Pro. Default. |
| `gemini-3.1-flash-image-preview` | Google AI native | Cheaper, faster, still good for simple diagrams |
| `gpt-image-2` | OpenAI native (`/v1/images/generations`) | Requires `OPENAI_API_KEY` |
| `openai/gpt-5.4-image-2` | OpenRouter chat-completions | The OpenRouter id for OpenAI's GPT-Image-2; about half the price of OpenAI direct |
| `google/gemini-3-pro-image-preview` | OpenRouter chat-completions | Same model via OpenRouter — useful if you don't have a direct Google AI key |

The dispatch rule inside the patched `visualizer_agent.py` is:

```python
if "gemini" in name and "/" not in name:
    # Google AI native
elif "gpt-image" in name and "/" not in name:
    # OpenAI native /v1/images/generations
elif "/" in name and "image" in name:
    # OpenRouter chat-completions image model
else:
    raise ValueError("Unsupported model")
```

## Fallback trigger

When `--auto-fallback` is on (default), the patched call wrapper retries with
the configured fallback model if **any** of the following matches:

| Signal | How matched |
|--------|-------------|
| HTTP status `429` | `getattr(exc, "status_code", None) == 429` |
| Error message contains `RESOURCE_EXHAUSTED` | substring (case-insensitive) |
| Error message contains `quota` | substring |
| Error message contains `spending cap` | substring |
| Error message contains `billing` | substring |
| Error message contains `monthly cap` | substring |
| `genai.errors.ResourceExhaustedError` | exception type |

The fallback itself does **not** retry on quota errors (to avoid infinite
loops): if the fallback also runs out, the call returns `["Error"]`.

## Logging

When a fallback fires, a single warning line is printed:

```
[image-backend] primary 'gemini-3-pro-image-preview' hit quota limit (
  RESOURCE_EXHAUSTED: monthly spending cap), retrying with fallback
  'openai/gpt-5.4-image-2'.
```

This is intentional — silently swapping backends would make later debugging
of cost spikes much harder.

## Disabling fallback for a single run

```bash
uv run scripts/generate.py ... --no-fallback
```

This is what you want for debugging quota issues, A/B comparing backends, or
when running cost-sensitive batch jobs where you'd rather fail loud than
quietly burn OpenRouter credit.
