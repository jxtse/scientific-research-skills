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
| **Deep research / complex questions** | Gemini deep research | Tavily + Exa |
| **Specific paper by title** | Semantic Scholar | Google Scholar (via Tavily) |
| **Papers by author** | Semantic Scholar (author search) | AMiner |
| **Chinese research community** | AMiner | Semantic Scholar |
| **Industry/applied papers** | Tavily (deep) | Exa semantic search |
| **Social buzz / trending papers** | Twitter/X (xreach) | Reddit |
| **Code implementations** | GitHub (gh search) | Exa (get_code_context) |
| **Finding similar papers** | Exa (semantic) | Semantic Scholar (citations) |

## Workflow

### Step 1: Understand the Query

Before searching, clarify:
- **Scope**: Broad survey vs. specific subtopic
- **Recency**: All time vs. last N years vs. latest only
- **Venue preference**: Top-tier only? Specific conference?
- **Quantity**: Top 5 vs. comprehensive survey
- **Depth**: Quick list vs. deep research with synthesis

### Step 2: Select Search Strategy

**Quick search (single engine):**
For simple, well-defined queries. Use Semantic Scholar or arXiv directly.

**Multi-engine search (2-3 engines in parallel):**
For broader topics. Run engines simultaneously, deduplicate results.

**Deep research (Gemini):**
For complex, multi-faceted research questions. Gemini deep research mode synthesizes across many sources and provides a structured analysis with citations. Use this when:
- The question spans multiple subfields
- You need synthesis, not just a list of papers
- The user explicitly asks for "deep research" or "comprehensive survey"

### Step 3: Execute Search

```bash
# Semantic Scholar — paper metadata, citations, author search
# Free, no API key needed
node scripts/search/semantic-scholar.mjs "query" -n 20

# arXiv — latest preprints, category filtering
# Free, no API key needed
node scripts/search/arxiv.mjs "query" -n 15 --sort submittedDate --cat cs.CL

# Tavily — general web search, AI-optimized
node scripts/search/search.mjs "query site:arxiv.org OR site:aclanthology.org" -n 10
node scripts/search/search.mjs "query" --deep  # deeper search mode

# Exa — semantic search, finding similar content
mcporter call 'exa.web_search_exa(query: "query", numResults: 10)'

# Gemini — deep research (for complex questions)
# Use gemini-3.1-pro model with web search grounding
# Prompt: "Survey the recent literature on [topic]. Identify key papers,
#          main approaches, and open problems. Cite specific papers."

# AMiner — Chinese academic community
# Uses AMINER_API_KEY
```

### Step 4: Deduplicate & Rank

Merge results across engines:
1. Deduplicate by title similarity (fuzzy match, >90% = same paper)
2. Rank by: citation count × recency × venue tier × relevance
3. Flag if a paper appears in multiple engines (higher confidence)

### Step 5: Present Results

Format as a ranked list with key metadata:

```
1. **[Title]** (Venue Year, Citations: N)
   Authors: [First author] et al.
   TL;DR: [1 sentence]
   Why relevant: [connection to user's query]

2. ...
```

### Step 6: Deep Dive (Optional)

If user wants to go deeper on any paper:
- Switch to paper-reading skill
- Or add to Zotero reading queue (use zotero-management skill)

## Search Tips

- **Use specific terminology**: "multi-agent reinforcement learning" > "MARL" > "agents working together"
- **Combine with venue filter**: Adding `venue:ACL` or category `cs.CL` dramatically improves precision
- **Check citation chains**: A highly-cited paper's references and citers are often gold
- **Cross-lingual**: For Chinese papers, try both English and Chinese queries
- **Date filter for SOTA**: Use `--sort submittedDate` on arXiv to find the latest approaches
- **Gemini for synthesis**: When you need to understand a field (not just list papers), use Gemini deep research to get a narrative overview first, then drill into specific papers

## Quality Signals

When ranking, weight these signals:
- **Citation count**: High for established work, less meaningful for papers < 6 months old
- **Venue tier**: ACL/EMNLP/NeurIPS/ICML > workshops > arXiv-only
- **Author reputation**: Check if senior authors are established in the field
- **Code availability**: Papers with code are more verifiable
- **Reproducibility**: Clear methodology sections and experimental details
