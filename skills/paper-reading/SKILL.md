---
name: paper-reading
description: >
  Structured paper reading workflow from skim to deep analysis to archival.
  Use when the user asks to read, analyze, summarize, or review a specific paper
  (from arXiv link, PDF, Zotero item, or title).
---

# Paper Reading

Structured workflow for reading academic papers efficiently.

## When to Use

- User shares an arXiv link or PDF and asks to read/summarize it
- User asks about a specific paper's contributions, methods, or results
- User wants a reading digest for their records
- User asks to compare a paper against related work

## Reading Levels

### Level 1: Quick Skim (2 min)
**When**: User just wants to know if a paper is worth reading

Output:
- Paper title, authors, venue, year
- One-paragraph summary (what problem, what method, what result)
- Key contribution in one sentence
- Relevance assessment to user's work
- Recommendation: Read / Skip / Skim only

### Level 2: Standard Read (10 min)
**When**: User wants to understand the paper's approach

Output:
- **Problem**: What gap does this address?
- **Method**: How do they solve it? (with key technical details)
- **Key innovation**: What's genuinely new vs. incremental?
- **Results**: Main numbers + comparison to baselines
- **Limitations**: What they don't do, acknowledged or not
- **Connections**: How does this relate to user's active projects?

### Level 3: Deep Analysis (30 min)
**When**: User is seriously considering building on this paper

Output:
- Everything from Level 2, plus:
- **Detailed methodology**: Step-by-step technical walkthrough
- **Reproducibility assessment**: Can you implement this from the paper alone?
- **Experimental design critique**: Are the baselines fair? Metrics appropriate?
- **Hidden assumptions**: What are they not saying?
- **Extension opportunities**: How could this be improved or adapted?
- **Key equations/algorithms**: Extracted and explained
- **Figure analysis**: What do the key figures actually show?

## Workflow

### Step 1: Obtain Paper

```
arXiv link → Download PDF, extract text
PDF file → Extract text directly
Paper title → Search Semantic Scholar → get arXiv link → download
Zotero item → Get from local library
```

### Step 2: Read at Requested Level

Follow the appropriate level template above. When in doubt, start with Level 2.

### Step 3: Store Digest

After reading, save the digest:
1. Store structured summary to local dashboard
2. If user confirms, add/update Zotero entry with notes

### Step 4: Connect to Context

- Link to user's active projects if relevant
- Suggest follow-up papers (from references or "cited by")
- Note if this paper supports or contradicts prior reads

## Reading Heuristics

**For ML/AI papers:**
- Jump to Table 1 (main results) first — if the numbers aren't impressive, calibrate expectations
- Check the ablation study — it reveals what actually matters in their method
- Read the limitations/future work section — often more honest than the intro
- Look at Appendix — important details are often buried there

**For methods papers:**
- Focus on Figure 1 (method overview) + Section 3 (method) + Table 1 (results)
- Skip related work on first pass — come back only if you need positioning context

**For empirical papers:**
- Focus on experimental setup, metrics, and statistical significance
- Check if baselines are fairly implemented (same hyperparameter search budget?)
- Look for cherry-picked examples in qualitative analysis

## Paper Comparison Mode

When user asks to compare two papers:

```
| Aspect       | Paper A          | Paper B          |
|--------------|------------------|------------------|
| Problem      |                  |                  |
| Method       |                  |                  |
| Data         |                  |                  |
| Key metric   |                  |                  |
| Advantage    |                  |                  |
| Limitation   |                  |                  |
```
