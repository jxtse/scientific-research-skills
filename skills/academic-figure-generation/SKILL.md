---
name: academic-figure-generation
description: >
  Generates publication-quality academic figures, framework diagrams, pipeline
  illustrations, system architectures, and method overviews from paper text and
  figure captions using a multi-agent pipeline (PaperBanana / PaperVizAgent).
  Use when the user asks to draw, generate, design, or create a figure for a paper, or refine an existing academic figure for a camera-ready submission.
---

# Academic Figure Generation

Generate publication-quality figures for academic papers using the
**PaperBanana** multi-agent pipeline (Retriever → Planner → Stylist →
Visualizer → Critic) with pluggable image backends.

## Image Backends

| Backend | Model id | Strengths | Pricing notes |
|---------|----------|-----------|---------------|
| **NanoBanana Pro** *(default)* | `gemini-3-pro-image-preview` | Clean, paper-style vector aesthetics; strong at simple block / pipeline diagrams | Google AI Studio monthly spending cap |
| **GPT-Image-2** *(fallback / explicit)* | `openai/gpt-5.4-image-2` | Best-in-class typography, dense layouts, multilingual text rendering, 2K output | OpenRouter pay-as-you-go (~$0.20–0.30 per 1K image) |

The selection logic is, in order of priority:

1. CLI flag `--image-model <id>`
2. Env var `PAPERBANANA_IMAGE_MODEL`
3. `configs/model_config.yaml` → `defaults.image_model_name`
4. Default: `gemini-3-pro-image-preview`

If `--auto-fallback` is on (the default) and the primary backend fails with a
quota / billing / rate-limit error, the pipeline automatically retries with
the configured fallback (default: `openai/gpt-5.4-image-2`). Use
`--no-fallback` while debugging.

See [`references/backend_routing.md`](references/backend_routing.md) for the
exact error patterns that trigger the fallback.

## Text Model

Independent from the image backend. Recommended setups:

- **Local copilot-api on `:4141`** (preferred when available — it routes
  through GitHub Copilot quota, so the text agents are effectively free):
  ```
  --text-model gemini-3.1-pro-preview     # or claude-opus-4.7, gpt-5.4
  --text-base-url http://127.0.0.1:4141/v1
  ```
- **Direct Google AI**: any `gemini-*` id, with `GOOGLE_API_KEY` set.
- **Anything OpenAI-compatible**: point `--text-base-url` at your endpoint.

## When to Use

- "Draw a figure for the paper"
- Need a method overview / framework diagram / pipeline illustration
- Need to visualize an architecture or system design
- Preparing camera-ready Figure 1 for an ACL/NeurIPS/EMNLP submission

## Workflow

### Step 1: Locate or install PaperBanana

PaperBanana is the underlying pipeline. Check for an existing local install:

```bash
ls /Users/richard/.openclaw/workspace/projects/PaperBanana/.venv/bin/python 2>/dev/null \
  || echo "PaperBanana not installed at default location"
```

If missing, install via:

```bash
git clone https://github.com/google-research/PaperBanana.git ~/PaperBanana
cd ~/PaperBanana
uv venv && uv pip install -r requirements.txt
```

Then point the skill at it via `--paperbanana-root <path>` or
`PAPERBANANA_ROOT` env var.

### Step 2: Apply the multi-backend patch (one-time)

PaperBanana ships with branches for `gemini-*` and `gpt-image-*` models only.
This skill ships a small patch in
[`scripts/patch_multibackend.py`](scripts/patch_multibackend.py) that adds:

- An OpenRouter chat-completions image client (for `openai/gpt-5.4-image-2`).
- A copilot-api / OpenAI-compatible text client (so non-Gemini text models can
  drive Planner/Stylist/Critic without rewriting the agents).
- Quota-aware automatic fallback for the image backend.

Apply it once:

```bash
uv run scripts/patch_multibackend.py --paperbanana-root /path/to/PaperBanana
```

The patch is idempotent — running it again on an already-patched checkout is a
no-op. See [`references/patch_overview.md`](references/patch_overview.md) for
what it changes.

### Step 3: Gather Input

You need two things:

1. **Method text**: The relevant section of the paper describing the approach
2. **Figure caption**: The target caption (e.g., "Figure 1: Overview of our
   proposed framework")

If the user only gives a vague request, ask for:

- What aspect of the method should the figure focus on?
- Style? (block diagram, flowchart, pipeline, architecture, comparison)
- Venue / column width? (ACL ≤ 7.5", NeurIPS single-column 5.5")

### Step 4: Generate

Use [`scripts/generate.py`](scripts/generate.py):

```bash
uv run scripts/generate.py \
  --method-file ./method.md \
  --caption "Figure 1: Overview of our framework" \
  --out-dir ./figures/v1 \
  --candidates 3 \
  --aspect-ratio 16:9
```

Common flags:

| Flag | Default | Notes |
|------|---------|-------|
| `--image-model` | `gemini-3-pro-image-preview` | NanoBanana Pro by default; pass `openai/gpt-5.4-image-2` for GPT-Image-2 |
| `--fallback-image-model` | `openai/gpt-5.4-image-2` | Used when primary backend quota-fails |
| `--auto-fallback` / `--no-fallback` | `--auto-fallback` | Toggle quota-triggered retry |
| `--text-model` | `gemini-3.1-pro-preview` | Drives Planner / Stylist / Critic |
| `--text-base-url` | `http://127.0.0.1:4141/v1` if reachable, else direct Google AI | OpenAI-compatible endpoint for text model |
| `--candidates` | `3` | Independent diagram candidates |
| `--max-critic-rounds` | `1` | How many critique → revise loops |
| `--exp-mode` | `demo_planner_critic` | `vanilla` skips the multi-agent flow (just method+caption → image) |
| `--retrieval` | `none` | Set `auto` to retrieve style references (more tokens) |
| `--aspect-ratio` | `16:9` | One of `21:9`, `16:9`, `3:2`, `1:1` |

### Step 5: Present & Iterate

- Show all candidates to the user
- Common refinements: color scheme, layout, label text, font size
- Re-run with adjusted `--candidates` count or a tweaked caption

### Step 6: Export

- PNG outputs land in `--out-dir` as `candidate_0.png`, `candidate_1.png`, …
- Convert to PDF for camera-ready: `magick candidate_0.png candidate_0.pdf`
  or use `cairosvg` / `inkscape` for true vector when the source is SVG/TikZ

## Style Guidelines

- **Color**: Consistent, colorblind-friendly palette
- **Fonts**: Match the paper's body font when possible (Times for ACL/EMNLP,
  Helvetica/Arial for many ML venues)
- **Labels**: Concise; no full sentences inside the diagram
- **Arrows**: Solid for data flow, dashed for optional / feedback loops
- **Whitespace**: Don't overcrowd — reviewers skim figures in seconds

## Common Figure Types

| Type | When to Use | Key Elements |
|------|-------------|-------------|
| **Pipeline / Flowchart** | Sequential processing | Boxes + arrows, L→R or T→B |
| **Architecture** | System overview | Nested boxes, clear module boundaries |
| **Comparison** | Before/after, baseline vs proposed | Side-by-side panels |
| **Ablation** | Component contributions | Bar charts or tables w/ highlighted rows |
| **Framework** | High-level conceptual overview | Abstract shapes, minimal detail |

## Troubleshooting

- **`429 RESOURCE_EXHAUSTED` on Gemini and `--no-fallback`**: hit Google AI
  Studio monthly cap. Either raise the cap, set
  `--image-model openai/gpt-5.4-image-2`, or remove `--no-fallback`.
- **`OpenRouter Client not initialized`**: missing `OPENROUTER_API_KEY` env
  var.
- **Empty `images` field from OpenRouter**: the model occasionally refuses
  prompts that look NSFW. Reword the caption.
- **Long latency (>5 min)**: most of the wall time is the image model. Lower
  `--candidates` or set `--max-critic-rounds 0` for faster iteration.

## References

- Backend routing & fallback rules: [`references/backend_routing.md`](references/backend_routing.md)
- Patch overview: [`references/patch_overview.md`](references/patch_overview.md)
- PaperBanana paper: https://huggingface.co/papers/2601.23265
- PaperBananaBench dataset: https://huggingface.co/datasets/dwzhu/PaperBananaBench
