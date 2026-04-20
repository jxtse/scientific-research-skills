# 🔬 Scientific Research Skills

High-level research methodology skills for AI coding agents.

> **Not another tool list.** Each skill encodes a *research workflow* — the kind of domain expertise that takes months to develop. Skills are written for AI agents to read and follow; this README is written for humans to configure and choose.

## Quick Start

### For AI Agents

If a user sends you this repo link, follow these steps:

1. Read this README to understand the available skills
2. Present each skill's name and one-line description to the user
3. Ask: "Which skills would you like to install? (all / select specific ones)"
4. For each selected skill, check if dependencies are met (see Setup section below)
5. If any API keys or tools are missing, guide the user through configuration
6. Copy the selected `SKILL.md` files to the appropriate location for your platform

### For Humans

1. Browse the [Skills](#skills) table below
2. Pick the skills relevant to your research workflow
3. Follow the [Setup](#setup) guide for your agent platform
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
| **[research-ideation](skills/research-ideation/)** | Go from empirical observation → research question → contribution framing. | None (methodology only) |
| **[experiment-design](skills/experiment-design/)** | Design experiments with proper baselines, ablations, and statistical methodology. | None (methodology only) |
| **[paper-writing](skills/paper-writing/)** | Paper writing workflow from outline to camera-ready. | None (methodology only) |

### Skill categories

- 🔧 **Tool-integrated** (literature-search, social-media-paper-triage, zotero-management, academic-figure-generation) — require external APIs or tools
- 📋 **Methodology-only** (paper-reading, related-work-survey, research-ideation, experiment-design, paper-writing) — pure workflow guidance, no external dependencies

---

## Setup

### Platform Installation

<details>
<summary><strong>OpenClaw</strong></summary>

Copy skill folders to the OpenClaw skills directory:

```bash
# Install all skills
cp -r skills/* ~/.openclaw/skills/

# Or install specific skills
cp -r skills/literature-search ~/.openclaw/skills/
cp -r skills/paper-reading ~/.openclaw/skills/
```

Skills are auto-discovered on next session. Each skill has a `SKILL.md` with YAML frontmatter that OpenClaw reads natively.

</details>

<details>
<summary><strong>Claude Code</strong></summary>

Append skill content to your project's `CLAUDE.md`:

```bash
# Option 1: Append specific skills to CLAUDE.md
echo "" >> CLAUDE.md
echo "# Research Skills" >> CLAUDE.md
cat skills/literature-search/SKILL.md >> CLAUDE.md
cat skills/paper-reading/SKILL.md >> CLAUDE.md
```

```bash
# Option 2: Reference skills directory in CLAUDE.md
echo "When doing research tasks, read the relevant SKILL.md from skills/ directory." >> CLAUDE.md
```

Or create custom commands:

```bash
mkdir -p .claude/commands
# Create a /research-search command
cp skills/literature-search/SKILL.md .claude/commands/research-search.md
```

</details>

<details>
<summary><strong>Codex</strong></summary>

Append skill content to `AGENTS.md`:

```bash
# Append to global AGENTS.md
cat skills/literature-search/SKILL.md >> ~/.codex/AGENTS.md

# Or to project-level AGENTS.md
cat skills/literature-search/SKILL.md >> ./AGENTS.md
```

</details>

<details>
<summary><strong>Other Agents</strong></summary>

Each `SKILL.md` is self-contained markdown. Feed it as system prompt or context to any LLM agent. The YAML frontmatter can be ignored — the markdown body contains all instructions.

</details>

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
4. **Platform-agnostic** — Works with OpenClaw, Claude Code, Codex, or any agent that reads markdown

---

## Contributing

This is a living repo. Skills are added as research workflows mature.

To contribute a new skill:
1. Create `skills/<skill-name>/SKILL.md`
2. Use the existing skills as format reference (YAML frontmatter + markdown body)
3. Focus on *when* and *why*, not just *how*
4. PR with a one-paragraph description of the workflow it encodes

## License

MIT
