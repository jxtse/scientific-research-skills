---
name: related-work-survey
description: >
  Conducts a systematic related-work / literature-survey / state-of-the-art
  review for a research question by defining survey dimensions, searching each
  axis, building a taxonomy of prior work, identifying the gap, and producing
  a positioning narrative for a paper's Related Work section. Goes beyond a
  flat paper list to deliver structured analysis. Use when the user is
  starting a new research project and needs to map the landscape, asks
  "what's been done on X?" or "how does my idea compare to existing work?",
  needs to write or revise a Related Work / Background / Prior Art section,
  wants to identify a research gap or position their contribution, or asks to
  build a taxonomy of approaches in a research area.
---

# Related Work Survey

Systematic literature survey for positioning a research contribution.

## When to Use

- User starts a new research project and needs landscape understanding
- User asks "what's been done on X?"
- User needs to write a related work section
- User wants to identify the gap their work fills

## Workflow

### Step 1: Define the Research Question

Work with the user to pin down:
- **Core question**: What specific problem are we solving?
- **Key concepts**: What are the 3-5 key terms/concepts?
- **Scope boundaries**: What's in scope vs. adjacent but out of scope?

### Step 2: Identify Survey Dimensions

Every research topic sits at an intersection of multiple dimensions. Identify 2-4 axes:

Example for "Neural-Symbolic Decomposition in LLM Agents":
- Axis 1: Neuro-symbolic integration approaches
- Axis 2: LLM agent architectures (harness, scaffolding)
- Axis 3: Adaptive/metacognitive planning
- Axis 4: Text analysis at scale (specific application)

### Step 3: Search Each Dimension

For each axis, use literature-search skill with targeted queries:

```
Axis 1 → "neuro-symbolic integration LLM reasoning 2024 2025"
Axis 2 → "LLM agent harness scaffolding architecture survey"
Axis 3 → "metacognitive planning adaptive tool use LLM"
Axis 4 → "large scale text analysis LLM code generation quality"
```

Collect 10-20 papers per axis, then deduplicate across axes.

### Step 4: Build the Taxonomy

Organize papers into a structured taxonomy:

```markdown
## Related Work Taxonomy

### 1. Neuro-Symbolic Integration
  1.1 Neural reasoning with symbolic verification
  1.2 Symbolic planning with neural execution
  1.3 Adaptive decomposition (our focus)

### 2. LLM Agent Architecture
  2.1 Harness engineering
  2.2 Self-evolving agents
  2.3 Meta-Harness optimization

### 3. ...
```

### Step 5: Identify the Gap

The gap is where your work lives — the intersection that no existing paper covers:

```
Paper A does X but not Y.
Paper B does Y but not X.
We do both X and Y, connected by Z.
```

### Step 6: Write the Narrative

Structure the related work section as a story:
1. **Context**: What's the broader field?
2. **Prior art per axis**: What has been done?
3. **Gap statement**: What's missing?
4. **Our position**: How do we fit in?

## Output Format

Deliver a structured document:

```markdown
# Related Work Survey: [Topic]

## Research Question
[1-2 sentences]

## Taxonomy
[Structured tree]

## Key Papers
| Paper | Axis | Key Contribution | Gap Relative to Us |
|-------|------|------------------|--------------------|
| ...   | ...  | ...              | ...                |

## Identified Gap
[Clear statement of what no existing work covers]

## Recommended Positioning
[How to frame our contribution relative to existing work]
```

## Principles

- **Be honest about overlap**: If someone has done something very similar, acknowledge it
- **Recent > old**: Prioritize 2024-2026 papers for positioning; cite older seminal works for foundations
- **Quality > quantity**: 20 well-chosen papers > 50 tangentially related ones
- **Track the conversation**: Note who cites whom — citation chains reveal intellectual lineage
- **Check workshops/findings**: Important early-stage work often appears in workshop papers
