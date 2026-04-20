---
name: social-media-paper-triage
description: >
  Extract, identify, and triage academic paper recommendations from social media
  links (小红书, WeChat公众号, Twitter/X, etc.). Use when the user forwards a
  social media post containing paper recommendations, or asks to find the original
  paper from a blog/post/thread.
---

# Social Media Paper Triage

Turn social media paper recommendations into actionable research items.

## When to Use

- User forwards a 小红书 post about a paper
- User shares a WeChat公众号 article discussing papers
- User shares a Twitter/X thread about a paper or method
- User asks "find the original paper from this link"
- User shares any blog post / newsletter that references academic papers

## Workflow

### Step 1: Extract Content from Platform

Use platform-specific tools to fetch the full content:

| Platform | Tool | Command |
|----------|------|---------|
| **小红书** | Agent Reach (XiaoHongShu) | `mcporter call 'xhs.get_note(note_url: "URL")'` |
| **WeChat公众号** | Agent Reach (WeChat) | `python3 ~/.agent-reach/.venv/bin/wechat_article.py "URL"` |
| **Twitter/X** | xreach | `xreach tweet URL --json` or `xreach thread URL --json` |
| **Reddit** | Agent Reach | `mcporter call 'reddit.read_post(url: "URL")'` |
| **Bilibili** | Agent Reach | `mcporter call 'bilibili.get_video_info(url: "URL")'` |
| **Any URL** | Jina Reader | `curl -s "https://r.jina.ai/URL"` |

### Step 2: Identify Papers

From the extracted content, identify all referenced papers:
- Look for: paper titles, arXiv IDs, DOIs, author names + year citations
- Distinguish between: the main paper being discussed vs. papers cited in passing
- Note: social media posts often use informal titles or translated titles

### Step 3: Find Original Sources

For each identified paper, find the authoritative source:

1. **arXiv search**: Check if it's on arXiv (most ML/AI papers are)
2. **Semantic Scholar**: Search by title for metadata + citation count
3. **Google Scholar** (via web search): Fallback for non-arXiv papers

Priority: arXiv PDF > conference proceedings > journal version

### Step 4: Summarize for Decision

Present a concise summary to the user:

```
📄 Paper: [Title]
👥 Authors: [First author] et al., [Year]
🏛 Venue: [Conference/Journal]
📊 Citations: [N]
🔗 Original: [arXiv/DOI link]
📱 Source: [social media link]

TL;DR: [2-3 sentence summary of what the paper does and why it matters]

Relevance to your work: [brief assessment based on user's research context]
```

### Step 5: User Decision → Action

Based on user's response:
- **"Add to reading queue"** → Add to Zotero `30_Reading Queue` with appropriate tag
- **"Not relevant"** → Done, no action
- **"Read it now"** → Switch to paper-reading skill
- **"Save for later"** → Add to Zotero with lower priority tag

## Key Principles

1. **Always find the original paper** — don't just summarize the social media post
2. **Don't auto-add to Zotero** — summarize first, let user decide
3. **Preserve the social media link** — add as a note/attachment in Zotero for provenance
4. **Assess relevance** — use knowledge of user's active projects to judge fit
5. **Batch processing** — if the post mentions multiple papers, triage all of them at once

## Common Gotchas

- WeChat articles often translate paper titles to Chinese — search by original English title
- 小红书 posts may summarize methods inaccurately — always verify against the original
- Twitter threads may reference preprints that have been updated/published since
- Some posts discuss methods without naming specific papers — ask user for clarification
