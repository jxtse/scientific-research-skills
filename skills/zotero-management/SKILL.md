---
name: zotero-management
description: >
  Manage a Zotero academic library with structured collections, tags, and workflows.
  Use when the user asks to add papers to Zotero, organize their library, check
  reading queue, or manage literature for a project.
---

# Zotero Library Management

Systematic management of an academic literature library via Zotero.

## When to Use

- User asks to add a paper to Zotero
- User asks to check their reading queue
- User wants to organize papers for a project
- User asks "what's in my library about X?"
- User asks to clean up or reorganize collections

## Library Structure

Standard collection hierarchy:

```
00_Inbox           → Newly added, unprocessed papers
10_Active Projects → Papers actively being used in current work
20_Background      → General domain knowledge, surveys, textbooks
30_Reading Queue   → Papers to read, prioritized
40_Archive         → Completed projects, historical reference
90_Meta            → Templates, style guides, writing resources
```

## Tag System

Use tags to cross-cut the collection hierarchy:

- **Project tags**: `#Inception`, `#AI-Scientist-BioAge`, `#ChemRetro`, `#CAST`
- **Status tags**: `#to-read`, `#reading`, `#read`, `#summarized`
- **Priority tags**: `#urgent`, `#high`, `#low`
- **Type tags**: `#survey`, `#method`, `#benchmark`, `#position-paper`

## API Access

Two access modes:

| Mode | Endpoint | Capability |
|------|----------|------------|
| **Local API** | `localhost:23119` | Read-only, fast, requires Zotero running |
| **Web API** | `api.zotero.org` | Read-write, works always, needs API key |

```bash
# Check if Zotero is running locally
curl -s http://localhost:23119/api/users/0/items?limit=1

# Web API (read-write)
curl -s -H "Zotero-API-Key: $ZOTERO_API_KEY" \
  "https://api.zotero.org/users/$ZOTERO_USER_ID/items?limit=5"
```

## Workflows

### Adding a Paper

1. **Find metadata**: Get title, authors, year, venue, DOI/arXiv ID
2. **Check for duplicates**: Search existing library by title
3. **Present summary to user**: Don't auto-add — confirm first
4. **Add to Zotero** via Web API with:
   - Correct item type (journalArticle, conferencePaper, preprint)
   - All available metadata fields
   - Collection: `30_Reading Queue` (default) or user-specified
   - Tags: project tag + `#to-read`
5. **Attach notes**: Source link (social media post, blog, etc.) as a note

### Checking Reading Queue

```bash
# Get items in Reading Queue collection
curl -s -H "Zotero-API-Key: $ZOTERO_API_KEY" \
  "https://api.zotero.org/users/$ZOTERO_USER_ID/collections/<COLLECTION_KEY>/items?limit=50"
```

Present as a prioritized list:
```
📚 Reading Queue (N papers)

🔴 Urgent:
1. [Paper Title] — added [date], tagged #Inception

🟡 High priority:
2. [Paper Title] — added [date], tagged #AI-Scientist-BioAge

⚪ Normal:
3. ...
```

### After Reading a Paper

1. Move from `30_Reading Queue` to `10_Active Projects` or `20_Background`
2. Update tag: `#to-read` → `#read` or `#summarized`
3. Add reading notes as a child note item
4. Link to project if relevant

### Project Literature Setup

When starting a new project:
1. Create a project tag (e.g., `#NewProject`)
2. Do initial literature search (use literature-search skill)
3. Batch-add relevant papers to `30_Reading Queue` with project tag
4. Prioritize: which papers must be read first?

## Key Principles

1. **Confirm before adding** — always show summary, let user decide
2. **Preserve provenance** — record where you found the paper (social media link, search query)
3. **One source of truth** — Zotero is the canonical library; don't maintain parallel lists
4. **Tags cross-cut collections** — a paper can be in one collection but tagged for multiple projects
5. **Regular maintenance** — periodically review Inbox and Reading Queue for stale items
