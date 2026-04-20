# 🔬 Scientific Research Skills

High-level, methodology-driven skills for AI-assisted scientific research.

**Not another tool list.** This is a curated collection of research *workflows* and *domain expertise* — the kind of know-how that takes months to develop but can be encoded into reusable skills for LLM agents.

## Philosophy

Most existing "AI for research" repos are tool catalogs: hundreds of specific utilities, most irrelevant to any given researcher. This repo takes a different approach:

- **High-level over low-level:** Each skill encodes a *methodology*, not just a tool invocation
- **Workflow over function:** Skills describe multi-step processes with decision points, not single API calls
- **Domain expertise over documentation:** Skills capture *when* and *why* to do something, not just *how*
- **Agent-native:** Designed to be loaded directly by OpenClaw, Claude Code, Codex, and other coding agents

## Skills

| Skill | Description | Status |
|-------|-------------|--------|
| [academic-figure-generation](skills/academic-figure-generation/) | Generate publication-quality figures from paper method text using multi-agent pipeline | ✅ Ready |
| [social-media-paper-triage](skills/social-media-paper-triage/) | Extract and triage paper recommendations from social media (小红书, WeChat, Twitter, etc.) | ✅ Ready |
| [literature-search](skills/literature-search/) | Multi-source academic paper search with adaptive engine selection | ✅ Ready |
| [paper-reading](skills/paper-reading/) | Structured paper reading workflow: skim → deep read → digest → archive | ✅ Ready |
| [related-work-survey](skills/related-work-survey/) | Systematic literature survey for a research question | ✅ Ready |
| [zotero-management](skills/zotero-management/) | Structured Zotero library management with collections, tags, and workflows | ✅ Ready |
| [experiment-design](skills/experiment-design/) | Design experiments with baselines, ablations, metrics, and statistical rigor | 🚧 Draft |
| [paper-writing](skills/paper-writing/) | Camera-ready paper writing workflow: outline → draft → revise → format | 🚧 Draft |
| [research-ideation](skills/research-ideation/) | From observation to research question to contribution framing | 🚧 Draft |

## How to Use

### With OpenClaw

Copy any skill folder into `~/.openclaw/skills/` and it will be auto-discovered:

```bash
cp -r skills/literature-search ~/.openclaw/skills/
```

### With Claude Code

Add the SKILL.md content to your project's `CLAUDE.md` or reference it in your prompt:

```
Read skills/literature-search/SKILL.md and follow it for this task.
```

### With Codex / Other Agents

Each skill's `SKILL.md` is self-contained. Feed it as context to any agent.

## Contributing

This is a living repo. Skills are added as research workflows mature. PRs welcome — but remember: methodology over tooling.

## License

MIT
