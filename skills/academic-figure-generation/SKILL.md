---
name: academic-figure-generation
description: >
  Generates publication-quality academic figures (framework diagrams,
  pipeline illustrations, system architectures, method overviews) from a
  paper's method text and a target caption, using a local PaperBanana
  multi-agent pipeline (Retriever → Planner → Stylist → Visualizer →
  Critic). Produces camera-ready PNG candidates suitable for ACL,
  NeurIPS, ICML, EMNLP, and similar venues. Use when the user asks to
  draw, design, or generate a figure for a paper, build a method /
  framework / pipeline / architecture diagram, or refine an existing
  figure for camera-ready submission.
---

# Academic Figure Generation

Thin CLI wrapper around **PaperBanana** (a.k.a. PaperVizAgent), a
multi-agent figure-generation pipeline for academic papers.

The skill provides exactly one script: `scripts/generate.py`. It feeds
your method text + caption into PaperBanana and writes N candidate PNGs.
Model selection and API keys come from PaperBanana's own
`configs/model_config.yaml` — the wrapper does not override them.

## One-time setup

1. **Clone PaperBanana** somewhere convenient:

   ```bash
   git clone https://github.com/dwzhu-pku/PaperBanana.git ~/PaperBanana
   cd ~/PaperBanana
   uv venv && uv pip install -r requirements.txt
   ```

2. **Configure `configs/model_config.yaml`** — set the image model and
   the matching API key. Two common setups:

   ```yaml
   defaults:
     image_model_name: "gemini-3-pro-image-preview"   # or "openai/gpt-5.4-image-2"
     model_name: "gemini-3.1-pro-preview"             # text model for Planner/Stylist/Critic

   api_keys:
     google_api_key: "..."        # required for Gemini models
     openrouter_api_key: ""       # required for openai/gpt-5.4-image-2
   ```

   Use Gemini if you have a Google AI key; use GPT-Image-2 via OpenRouter
   if you have an OpenRouter key. Pick one — there's nothing else to wire
   up.

## Workflow

### Step 1: Gather inputs

You need:

1. **Method text**: the relevant section of the paper describing the
   approach (`./method.md` or `./method.tex`).
2. **Figure caption**: the target caption, e.g. `"Figure 1: Overview of
   our framework"`.

If the user only gives a vague request, ask:

- What aspect of the method should the figure focus on?
- Style? (block diagram, flowchart, pipeline, architecture, comparison)
- Venue / column width? (ACL ≤ 7.5", NeurIPS single-column 5.5")

### Step 2: Generate

```bash
~/PaperBanana/.venv/bin/python scripts/generate.py \
  --paperbanana-root ~/PaperBanana \
  --method-file ./method.md \
  --caption "Figure 1: Overview of our framework" \
  --out-dir ./figures/v1 \
  --candidates 3 \
  --aspect-ratio 16:9
```

| Flag | Default | Notes |
|------|---------|-------|
| `--paperbanana-root` | (required) | Path to your PaperBanana checkout |
| `--method-file` | (required) | Method section as a text/markdown file |
| `--caption` | (required) | Target figure caption |
| `--out-dir` | (required) | Where PNGs land |
| `--candidates` | `3` | Independent diagram candidates |
| `--max-concurrent` | `2` | Cap concurrent runs (be gentle on quota) |
| `--exp-mode` | `demo_full` | Full pipeline (Planner+Stylist+Visualizer+Critic). Use `demo_planner_critic` to skip Stylist, or `vanilla` for single-shot. |
| `--aspect-ratio` | `16:9` | One of `21:9`, `16:9`, `3:2`, `1:1` |
| `--max-critic-rounds` | `2` | Critique → revise loops (early-exits if critic says "No changes needed") |

### Step 3: Present & iterate

- Show all candidates to the user.
- Common refinements: color scheme, layout, label text, font size.
- Re-run with a tweaked caption or more candidates.

### Step 4: Export

- PNGs are written as `candidate_0.png`, `candidate_1.png`, … in `--out-dir`.
- For camera-ready PDFs: `magick candidate_0.png candidate_0.pdf`.

## Style guidelines

- **Color**: consistent, colorblind-friendly palette
- **Fonts**: match the paper's body font (Times for ACL/EMNLP,
  Helvetica/Arial for many ML venues)
- **Labels**: concise; no full sentences inside the diagram
- **Arrows**: solid for data flow, dashed for optional / feedback loops
- **Whitespace**: don't overcrowd — reviewers skim figures in seconds

## Common figure types

| Type | When to use | Key elements |
|------|-------------|--------------|
| Pipeline / Flowchart | Sequential processing | Boxes + arrows, L→R or T→B |
| Architecture | System overview | Nested boxes, clear module boundaries |
| Comparison | Before/after, baseline vs proposed | Side-by-side panels |
| Ablation | Component contributions | Bar charts, highlighted rows |
| Framework | High-level conceptual overview | Abstract shapes, minimal detail |

## Troubleshooting

- **`429 RESOURCE_EXHAUSTED` on Gemini**: monthly Google AI Studio
  spending cap hit. Raise it at <https://ai.studio/spend> or switch
  `image_model_name` to `openai/gpt-5.4-image-2` and set
  `OPENROUTER_API_KEY`.
- **`OpenRouter Client not initialized`**: `OPENROUTER_API_KEY` not in env
  and `openrouter_api_key` not in yaml.
- **No PNGs in output dir**: check `out_dir/results.json` for the raw
  per-candidate response and any error messages.
- **Long latency (>5 min)**: most wall time is the image model. Lower
  `--candidates` or use `--exp-mode vanilla` for faster iteration.

## Links

- PaperBanana repo: <https://github.com/dwzhu-pku/PaperBanana>
- PaperVizAgent (Google Research version of the same project): <https://github.com/google-research/papervizagent>
