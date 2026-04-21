---
name: academic-figure-generation
description: >
  Generates publication-quality academic figures, framework diagrams, pipeline
  illustrations, system architectures, and method overviews from paper text and
  figure captions using a multi-agent pipeline (PaperBanana). Produces
  camera-ready PNG/PDF figures suitable for ACL, NeurIPS, ICML, EMNLP, and
  similar venues. Use when the user asks to draw, generate, design, or create a
  figure for a paper, build a method/architecture/framework/pipeline diagram,
  visualize a model or system, prepare a Figure 1 / overview diagram, render a
  TikZ or matplotlib figure for a manuscript, or refine an existing academic
  figure for a camera-ready submission.
---

# Academic Figure Generation

Generate publication-quality figures for academic papers using a multi-agent pipeline.

## When to Use

- User asks to "draw a figure for the paper"
- Need a method overview / framework diagram / pipeline illustration
- Need to visualize an architecture or system design
- Preparing camera-ready figures for submission

## Workflow

### Step 1: Gather Input

You need two things:
1. **Method text**: The relevant section of the paper describing the approach (Markdown OK)
2. **Figure caption**: The target caption for the figure (e.g., "Figure 1: Overview of our proposed framework")

If the user only provides a vague request, ask for:
- What aspect of the method should the figure focus on?
- What style? (block diagram, flowchart, pipeline, architecture, comparison table)
- What venue format? (single-column, double-column, width constraints)

### Step 2: Generate Candidates

Use the PaperBanana pipeline to generate multiple candidates (default: 3).

The pipeline has 5 agents:
1. **Retriever** — finds similar published figures as style references
2. **Planner** — creates a layout plan from the method text
3. **Stylist** — selects color palette, fonts, and visual style
4. **Visualizer** — generates the actual figure (Python/matplotlib/tikz)
5. **Critic** — evaluates and scores each candidate

### Step 3: Present & Iterate

- Show all candidates to the user
- Ask which direction to refine
- Common refinements: color scheme, layout, label text, font size, resolution

### Step 4: Export

- Export as PNG (300 DPI for review) or PDF (vector for camera-ready)
- Ensure the figure fits within the venue's column width requirements

## Style Guidelines

- **Color**: Use a consistent, colorblind-friendly palette
- **Fonts**: Match the paper's body font when possible (e.g., Times New Roman for ACL/EMNLP)
- **Labels**: Keep text concise; no full sentences in diagrams
- **Arrows**: Use consistent arrow styles (solid for data flow, dashed for optional/feedback)
- **Whitespace**: Don't overcrowd; leave breathing room between components

## Common Figure Types

| Type | When to Use | Key Elements |
|------|-------------|-------------|
| **Pipeline/Flowchart** | Sequential processing steps | Boxes + arrows, left-to-right or top-to-bottom |
| **Architecture** | System overview with multiple components | Nested boxes, clear module boundaries |
| **Comparison** | Before/after, baseline vs. proposed | Side-by-side panels with shared axes |
| **Ablation** | Showing component contributions | Bar charts or tables with highlighted rows |
| **Framework** | High-level conceptual overview | Abstract shapes, minimal detail |

## Dependencies

- PaperBanana pipeline (local deployment)
- Python with matplotlib, tikz support
- For style references: access to published paper figures

## Notes

- Always generate multiple candidates — the first attempt is rarely the best
- Venue-specific requirements matter (ACL: max 7.5" width; NeurIPS: 5.5" for single-column)
- When in doubt, simpler is better — reviewers skim figures in seconds
