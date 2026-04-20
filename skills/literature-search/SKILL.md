---
name: literature-search
description: >
  Multi-source academic literature search with adaptive engine selection.
  Use when the user asks to find papers on a topic, search for related work,
  survey a research area, or needs to find specific papers by title/author/venue.
---

# Literature Search

Systematic, multi-engine academic paper search.

## When to Use

- User asks "find papers about X"
- User needs related work for a new project
- User wants to know the state of the art on a topic
- User asks for papers from a specific venue/author/year

## Engine Selection

Choose engines based on the search goal:

| Goal | Primary Engine | Supplementary |
|------|---------------|---------------|
| **Broad topic survey** | Semantic Scholar | arXiv, Tavily |
| **Latest preprints** | arXiv (sort by submittedDate) | Semantic Scholar |
| **Specific paper by title** | Semantic Scholar | Google Scholar (via Tavily) |
| **Papers by author** | Semantic Scholar (author search) | AMiner |
| **Chinese research community** | AMiner | Semantic Scholar |
| **Industry/applied papers** | Tavily (deep) | Exa semantic search |
| **Social buzz / trending** | Twitter/X (xreach) | Reddit |
| **Code implementations** | GitHub (gh search) | Exa (get_code_context) |

## Workflow

### Step 1: Understand the Query

Before searching, clarify:
- **Scope**: Broad survey vs. specific subtopic
- **Recency**: All time vs. last N years vs. latest only
- **Venue preference**: Top-tier only? Specific conference?
- **Quantity**: Top 5 vs. comprehensive survey

### Step 2: Multi-Engine Search

Run 2-3 engines in parallel for coverage:

```bash
# Semantic Scholar
node scripts/search/semantic-scholar.mjs "query" -n 20

# arXiv (latest)
node scripts/search/arxiv.mjs "query" -n 15 --sort submittedDate --cat cs.CL

# Tavily (broader web)
node scripts/search/search.mjs "query site:arxiv.org OR site:aclanthology.org" -n 10
```

### Step 3: Deduplicate & Rank

Merge results across engines:
1. Deduplicate by title similarity (fuzzy match, >90% = same paper)
2. Rank by: citation count × recency × venue tier × relevance
3. Flag if a paper appears in multiple engines (higher confidence)

### Step 4: Present Results

Format as a ranked list with key metadata:

```
1. **[Title]** (Venue Year, Citations: N)
   Authors: [First author] et al.
   TL;DR: [1 sentence]
   Why relevant: [connection to user's query]

2. ...
```

### Step 5: Deep Dive (Optional)

If user wants to go deeper on any paper:
- Switch to paper-reading skill
- Or add to Zotero reading queue

## Search Tips

- **Use specific terminology**: "multi-agent reinforcement learning" > "MARL" > "agents working together"
- **Combine with venue filter**: Adding `venue:ACL` or category `cs.CL` dramatically improves precision
- **Check citation chains**: A highly-cited paper's references and citers are often gold
- **Cross-lingual**: For Chinese papers, try both English and Chinese queries
- **Date filter for SOTA**: Use `--sort submittedDate` on arXiv to find the latest approaches

## Quality Signals

When ranking, weight these signals:
- **Citation count**: High for established work, less meaningful for papers < 6 months old
- **Venue tier**: ACL/EMNLP/NeurIPS/ICML > workshops > arXiv-only
- **Author reputation**: Check if senior authors are established in the field
- **Code availability**: Papers with code are more verifiable
- **Reproducibility**: Clear methodology sections and experimental details
