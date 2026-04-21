# 🔬 Scientific Research Skills

High-level research methodology skills for AI coding agents.

> **Not another tool list.** Each skill encodes a *research workflow* — the kind of domain expertise that takes months to develop. Skills are written for AI agents to read and follow; this README is written for humans to configure and choose.

[中文版本 (Chinese)](README_CN.md)

## Quick Start

### For AI Agents

If a user sends you this repo link, follow this onboarding flow. **Do not skip the post-install configuration step** — many skills are non-functional without API keys, and silently installed skills are worse than uninstalled ones.

#### Step 1 — Introduce the skills

Read this README, then present each skill's name and one-line description to the user. Group them by category (🔧 tool-integrated vs 📋 methodology-only) so the user understands which ones will require configuration.

#### Step 2 — Confirm what to install

Ask: *"Which skills would you like to install? (all / select specific ones)"*

#### Step 3 — Install

Copy the selected skill folders to the appropriate location for your platform:
- **OpenClaw**: `~/.openclaw/skills/`
- **Claude Code**: `~/.claude/skills/` (user-level) or `.claude/skills/` (project-level)
- **Codex**: `~/.agents/skills/` (user-level) or `.agents/skills/` (project-level)

#### Step 4 — ⚠️ Post-install configuration (do not skip)

After installation, **explicitly notify the user** which installed skills require configuration before they will work. Use this template:

> ✅ Installed: `skill-a`, `skill-b`, `skill-c`
>
> ⚠️ Heads up — the following skills need configuration before use:
> - **`skill-a`** requires: TAVILY_API_KEY (free tier available)
> - **`skill-c`** requires: Zotero API key + User ID
>
> Want me to walk you through setting these up now? I can do them one by one.

Then, for each skill the user agrees to configure, **walk them through it interactively**:

1. **Check existing config first** — Run `echo $TAVILY_API_KEY` (or equivalent) to see if it's already set. If yes, skip to verification.
2. **Explain what the key is for** — One sentence on what the skill will use it for.
3. **Provide the signup link** — Give the direct URL (see [Dependencies](#dependencies) below). Wait for the user to obtain the key.
4. **Help them set it persistently** — Append the `export` line to their shell profile (`~/.zshrc` for zsh, `~/.bashrc` for bash). Don't just `export` in the current shell — that won't survive a restart.
5. **Verify** — Run a quick test (e.g., a 1-result search) to confirm the key works. If it fails, debug before moving on.
6. **Move to the next skill** — Repeat until all configurable skills are set up.

**Per-skill configuration cheat sheet:**

| Skill | What to configure | Where to get it | Required? |
|-------|------------------|-----------------|-----------|
| `literature-search` | At least one of: `TAVILY_API_KEY`, `EXA_API_KEY`, `GEMINI_API_KEY`, `AMINER_API_KEY` | See [Search Engines](#search-engines-for-literature-search). Semantic Scholar + arXiv work with no key. | At least one recommended |
| `social-media-paper-triage` | Jina Reader (no key) is enough for most URLs. For Twitter/X: install [xreach](https://github.com/xreach/xreach). For 小红书/微博/微信: install [Agent Reach](https://github.com/Panniantong/Agent-Reach). | See [Social Media Reading](#social-media-reading-for-social-media-paper-triage) | Optional unless using gated platforms |
| `zotero-management` | `ZOTERO_API_KEY` + `ZOTERO_USER_ID` | [zotero.org/settings/keys](https://www.zotero.org/settings/keys) | Required |
| `academic-figure-generation` | [PaperBanana](https://github.com/paperbanana/PaperBanana) local deployment | See skill's SKILL.md | Required |
| `paper-reading` | None | — | None |
| `related-work-survey` | Inherits `literature-search` config | — | Configure `literature-search` first |

#### Step 5 — Confirm completion

After configuration, summarize: which skills are fully working, which are installed but waiting on config the user wants to defer, and how to invoke each one in their agent.

#### Configuration etiquette

- **Never assume keys are set.** Always check.
- **Never write secrets to git-tracked files** (e.g., project-level `.env` without `.gitignore`).
- **Don't ask for keys all at once.** Walk through one skill at a time so the user isn't overwhelmed.
- **If the user wants to skip a config**, install the skill anyway but mark it as "⚠️ installed but not configured" so they remember later.

### For Humans

1. Browse the [Skills](#skills) table below
2. Pick the skills relevant to your research workflow
3. Follow the [Installation](#installation) guide for your agent platform
4. Configure any required [API keys and dependencies](#dependencies)

---

## Skills

| Skill | What it does | Dependencies |
|-------|-------------|--------------|
| **[literature-search](skills/literature-search/)** | Multi-engine academic paper search with adaptive engine selection. Covers Semantic Scholar, arXiv, Tavily, Exa, Gemini deep research, and more. | At least one search engine API key |
| **[paper-reading](skills/paper-reading/)** | Three-level paper reading (skim → read → deep analysis) with structured digest output. | PDF access |
| **[social-media-paper-triage](skills/social-media-paper-triage/)** | Extract paper recommendations from social media (小红书, WeChat, Twitter/X, etc.), find original sources, and triage for relevance. | Agent Reach or Jina Reader |
| **[related-work-survey](skills/related-work-survey/)** | Systematic literature survey: define dimensions → search each axis → build taxonomy → identify gap → position your contribution. | literature-search skill |
| **[zotero-management](skills/zotero-management/)** | Structured Zotero library management with collections, tags, project-based organization. | Zotero + API key |
| **[academic-figure-generation](skills/academic-figure-generation/)** | Generate publication-quality figures from method text using multi-agent pipeline (PaperBanana). | PaperBanana local deployment |


### Skill categories

- 🔧 **Tool-integrated** — require external APIs or tools: literature-search, social-media-paper-triage, zotero-management, academic-figure-generation
- 📋 **Methodology-only** — pure workflow guidance, no dependencies: paper-reading, related-work-survey

---

## Installation

Each skill follows the [open agent skills standard](https://agentskills.io/): a folder with a `SKILL.md` (YAML frontmatter + markdown instructions) plus optional `scripts/`, `references/`, and `assets/` directories. This format is natively supported by **OpenClaw**, **Claude Code**, and **Codex**.

### Install all skills

```bash
# Clone the repo
git clone https://github.com/jxtse/scientific-research-skills.git
cd scientific-research-skills

# OpenClaw
cp -r skills/* ~/.openclaw/skills/

# Claude Code (user-level, available in all projects)
cp -r skills/* ~/.claude/skills/

# Codex (user-level, available in all repos)
cp -r skills/* ~/.agents/skills/
```

### Install specific skills

```bash
# Example: install only literature-search and paper-reading

# OpenClaw
cp -r skills/literature-search ~/.openclaw/skills/
cp -r skills/paper-reading ~/.openclaw/skills/

# Claude Code
cp -r skills/literature-search ~/.claude/skills/
cp -r skills/paper-reading ~/.claude/skills/

# Codex
cp -r skills/literature-search ~/.agents/skills/
cp -r skills/paper-reading ~/.agents/skills/
```

### Project-level vs user-level

| Scope | OpenClaw | Claude Code | Codex |
|-------|----------|-------------|-------|
| **User-level** (all projects) | `~/.openclaw/skills/` | `~/.claude/skills/` | `~/.agents/skills/` |
| **Project-level** (single repo) | — | `.claude/skills/` | `.agents/skills/` |

Skills are auto-discovered by all three platforms. No restart needed for OpenClaw; restart Claude Code or Codex if a new skill doesn't appear.

### Other agents

Each `SKILL.md` is self-contained markdown. For agents that don't support the skills standard, feed the SKILL.md content as system prompt or context directly.

---

## Dependencies

### Search Engines (for literature-search)

You don't need all of them. Pick based on your needs:

| Engine | What it's good for | API Key |
|--------|-------------------|---------|
| **Semantic Scholar** | Paper metadata, citations, author search | Free, no key needed |
| **arXiv** | Latest preprints, category filtering | Free, no key needed |
| **Tavily** | General web search, AI-optimized results | [tavily.com](https://tavily.com) → free tier available |
| **Exa** | Semantic search, finding similar content | [exa.ai](https://exa.ai) → free tier available |
| **Gemini** | Deep research mode, synthesis across sources | [ai.google.dev](https://ai.google.dev) → free tier available |
| **AMiner** | Chinese academic community, scholar profiles | [open.aminer.cn](https://open.aminer.cn) → free with token |

**Minimum recommended:** Semantic Scholar (free) + arXiv (free) + one of Tavily/Exa.

```bash
# Set API keys in your shell profile (~/.zshrc or ~/.bashrc)
export TAVILY_API_KEY="tvly-..."
export EXA_API_KEY="..."
export GEMINI_API_KEY="..."     # Optional: for deep research
export AMINER_API_KEY="..."     # Optional: for Chinese academic search
```

### Social Media Reading (for social-media-paper-triage)

| Platform | Tool | Setup |
|----------|------|-------|
| **Any URL** | [Jina Reader](https://jina.ai/reader/) | No setup — `curl https://r.jina.ai/URL` |
| **Twitter/X** | [xreach](https://github.com/xreach/xreach) | `npm i -g xreach` + browser cookie auth |
| **小红书/微博/微信** | [Agent Reach](https://github.com/Panniantong/Agent-Reach) | Docker + platform-specific auth |

**Minimum recommended:** Jina Reader (zero config, works for most URLs).

### Zotero (for zotero-management)

1. Install [Zotero](https://www.zotero.org/download/)
2. Create API key: [zotero.org/settings/keys](https://www.zotero.org/settings/keys)
3. Find your User ID: shown on the same settings page

```bash
export ZOTERO_API_KEY="..."
export ZOTERO_USER_ID="..."
```

### Academic Figure Generation (for academic-figure-generation)

Requires [PaperBanana](https://github.com/paperbanana/PaperBanana) local deployment. See the skill's SKILL.md for setup details.

---

## Philosophy

**Why this repo exists:**

Existing "AI for research" repos (like `claude-scientific-skills`) catalog hundreds of specific tools. Most are irrelevant to any given researcher, and they describe *what* a tool does, not *when* or *why* to use it.

This repo encodes **research methodology** — the decision-making process that experienced researchers internalize over years:

- *When* to skim vs. deep-read a paper
- *How* to systematically survey a field and find your positioning
- *Which* search engine to use for which type of query
- *How* to go from a vague observation to a concrete research contribution

Each skill is a workflow, not a function call.

**Design principles:**

1. **For AI, not for show** — Skills are written as agent instructions, not human documentation
2. **High-level over low-level** — Methodology over tool invocation
3. **Modular** — Pick only what you need
4. **Cross-platform** — Same SKILL.md format works with OpenClaw, Claude Code, Codex, and any agent

---

## Contributing

This is a living repo. Skills are added as research workflows mature.

To contribute a new skill:
1. Create `skills/<skill-name>/SKILL.md`
2. Use the existing skills as format reference (YAML frontmatter + markdown body)
3. Focus on *when* and *why*, not just *how*
4. Optionally add `scripts/`, `references/`, or `assets/` directories
5. PR with a one-paragraph description of the workflow it encodes

## License

MIT
