# 🔬 科研技能库 (Scientific Research Skills)

面向 AI 编程助手的高阶科研方法论技能库。

> **不是又一个工具清单。** 每个 skill 封装的是一套*研究工作流* -- 那种需要数月经验才能沉淀的领域知识。Skill 文件写给 AI agent 阅读和执行;本文档写给人类配置和选择。

[English Version](README.md)

## 快速开始

### 给 AI Agent

如果用户把这个仓库链接发给你，按以下流程引导他。**安装完成后的配置步骤不要跳过** —— 很多 skills 没有 API key 就用不了，缺配置还装了一堆比不装还糟。

#### 第 1 步 — 介绍 skills

读完本 README，然后给用户呈现每个 skill 的名称和一句话描述。按分类呈现（🔧 工具集成型 vs 📋 纯方法论型），让用户一眼看出哪些需要配置。

#### 第 2 步 — 确认安装范围

问：*“你想安装哪些 skills？（全部 / 选择特定几个）”*

#### 第 3 步 — 安装

将选中的 skill 文件夹复制到对应平台目录：
- **OpenClaw**: `~/.openclaw/skills/`
- **Claude Code**: `~/.claude/skills/`（用户级）或 `.claude/skills/`（项目级）
- **Codex**: `~/.agents/skills/`（用户级）或 `.agents/skills/`（项目级）

#### 第 4 步 — ⚠️ 安装后配置引导（不要跳过）

安装完毕后，**主动提醒用户** 哪些已安装的 skills 需要配置才能使用。参考以下模板：

> ✅ 已安装：`skill-a`、`skill-b`、`skill-c`
>
> ⚠️ 提醒你一下 —— 以下 skills 需要配置后才能使用：
> - **`skill-a`** 需要：TAVILY_API_KEY（有免费额度）
> - **`skill-c`** 需要：Zotero API key + User ID
>
> 要我现在一步一步带你配吗？可以一个一个来。

然后，对于用户同意配置的每个 skill，**交互式地一步一步带他走完**：

1. **先检查现有配置** — 运行 `echo $TAVILY_API_KEY`（或对应命令）看是否已设置。如已设，跳到验证步骤。
2. **解释这个 key 是干什么的** — 一句话说明 skill 会用它做什么。
3. **提供注册链接** — 给出直接 URL（见下方 [依赖配置](#依赖配置)）。等用户获取 key。
4. **帮他永久化写入** — 将 `export` 语句追加到 shell 配置文件（zsh 用 `~/.zshrc`，bash 用 `~/.bashrc`）。不要只在当前 shell `export` —— 重启后就没了。
5. **验证** — 跑一个快速测试（比如一条返回结果的搜索）确认 key 生效。如果失败，先 debug 再继续。
6. **下一个 skill** — 重复直到所有需配置的 skills 都完成。

**各 skill 配置速查表：**

| Skill | 需配置项 | 获取方式 | 必需？ |
|-------|---------|---------|---------|
| `literature-search` | 以下任意一个：`TAVILY_API_KEY`、`EXA_API_KEY`、`GEMINI_API_KEY`、`AMINER_API_KEY` | 见[搜索引擎](#搜索引擎-用于-literature-search)。Semantic Scholar + arXiv 免配置。 | 至少配一个 |
| `paper-fulltext-harvest` | 可选：`ELSEVIER_API_KEY`+`ELSEVIER_INSTTOKEN`、`WILEY_TDM_TOKEN`、`SPRINGER_API_KEY`、`UNPAYWALL_EMAIL`、`CROSSREF_MAILTO`、`OPENALEX_MAILTO` | 见[出版商 TDM Keys](#出版商-tdm-keys-paper-fulltext-harvest-用)。仅需邮箱即可走 OA-only 模式。 | 付费文献需要 |
| `social-media-paper-triage` | 大多数 URL 用 Jina Reader（免配置）即可。Twitter/X 需装 [xreach](https://github.com/xreach/xreach)；小红书/微博/微信需装 [Agent Reach](https://github.com/Panniantong/Agent-Reach)。 | 见[社交媒体阅读](#社交媒体阅读-用于-social-media-paper-triage) | 限制平台才需 |
| `zotero-management` | `ZOTERO_API_KEY` + `ZOTERO_USER_ID` | [zotero.org/settings/keys](https://www.zotero.org/settings/keys) | 必需 |
| `academic-figure-generation` | [PaperBanana](https://github.com/paperbanana/PaperBanana) 本地部署 | 见该 skill 的 SKILL.md | 必需 |
| `paper-reading` | 无 | — | 无 |
| `related-work-survey` | 复用 `literature-search` 配置 | — | 先配好 `literature-search` |

#### 第 5 步 — 确认完成

配置完后，总结一下：哪些 skills 现在可用、哪些已装但用户选择稍后再配、以及在 agent 中如何调用每个 skill。

#### 配置礼仪

- **不要假设 key 已设置。** 每次都检查。
- **不要把密钥写入 git 跟踪的文件**（如项目级 `.env` 且未 `.gitignore`）。
- **不要一次问完所有 key。** 一个 skill 一个来，别让用户被淹没。
- **如果用户想跳过某个配置**，skill 还是装上，但标记为“⚠️ 已安装但未配置”让用户后续记得补。

### 给人类

1. 浏览下方 [Skills 列表](#skills-列表)
2. 选择适合你研究工作流的 skills
3. 按照[安装指南](#安装)操作
4. 配置所需的 [API key 和依赖](#依赖配置)

---

## Skills 列表

| Skill | 功能 | 依赖 |
|-------|------|------|
| **[literature-search](skills/literature-search/)** | 多引擎自适应学术文献搜索,覆盖 Semantic Scholar、arXiv、Tavily、Exa、Gemini 深度搜索等 | 至少一个搜索引擎 API key |
| **[paper-reading](skills/paper-reading/)** | 三级论文阅读法(快速扫描 → 标准阅读 → 深度分析),结构化摘要输出 | PDF 访问 |
| **[paper-fulltext-harvest](skills/paper-fulltext-harvest/)** | 从 DOI 列表批量下载论文全文 (PDF/XML)。自动路由到出版商 TDM API (Elsevier、Wiley、Springer)、OA 聚合器 (Unpaywall、OpenAlex、Crossref)，以及为 Cloudflare 保护出版商提供浏览器回退方案。 | 可选：付费内容需出版商 TDM keys |
| **[social-media-paper-triage](skills/social-media-paper-triage/)** | 从社交媒体(小红书、微信公众号、Twitter/X 等)提取论文推荐,查找原文,评估相关性 | Agent Reach 或 Jina Reader |
| **[related-work-survey](skills/related-work-survey/)** | 系统性文献调研:定义维度 → 分轴搜索 → 构建分类体系 → 识别研究空白 → 定位贡献 | literature-search skill |
| **[zotero-management](skills/zotero-management/)** | 结构化 Zotero 文献库管理,含 collection、标签、项目化组织 | Zotero + API key |
| **[academic-figure-generation](skills/academic-figure-generation/)** | 从论文方法描述生成出版级质量的学术图表(PaperBanana 多 agent pipeline) | PaperBanana 本地部署 |

### Skill 分类

- 🔧 **需要外部工具** - literature-search、social-media-paper-triage、zotero-management、academic-figure-generation、paper-fulltext-harvest
- 📋 **纯方法论** - paper-reading、related-work-survey

---

## 安装

每个 skill 遵循 [开放 agent 技能标准](https://agentskills.io/):一个包含 `SKILL.md`(YAML 头 + markdown 正文)的文件夹,可选附带 `scripts/`、`references/`、`assets/` 目录。**OpenClaw**、**Claude Code** 和 **Codex** 原生支持此格式。

### 安装全部

```bash
git clone https://github.com/jxtse/scientific-research-skills.git
cd scientific-research-skills

# OpenClaw
cp -r skills/* ~/.openclaw/skills/

# Claude Code(用户级,所有项目可用)
cp -r skills/* ~/.claude/skills/

# Codex(用户级,所有仓库可用)
cp -r skills/* ~/.agents/skills/
```

### 安装特定 skill

```bash
# 示例:只安装 literature-search 和 paper-reading

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

### 用户级 vs 项目级

| 范围 | OpenClaw | Claude Code | Codex |
|------|----------|-------------|-------|
| **用户级**(所有项目) | `~/.openclaw/skills/` | `~/.claude/skills/` | `~/.agents/skills/` |
| **项目级**(单个仓库) | - | `.claude/skills/` | `.agents/skills/` |

三个平台均自动发现 skills。OpenClaw 无需重启;Claude Code 和 Codex 若未显示新 skill 请重启。

### 其他 Agent

每个 `SKILL.md` 是自包含的 markdown 文件。对于不支持 skills 标准的 agent,直接将 SKILL.md 内容作为系统提示或上下文喂入即可。

---

## 依赖配置

### 搜索引擎(literature-search 用)

不需要全部安装,按需选择:

| 引擎 | 擅长什么 | API Key |
|------|---------|---------|
| **Semantic Scholar** | 论文元数据、引用关系、作者搜索 | 免费,无需 key |
| **arXiv** | 最新预印本、分类过滤 | 免费,无需 key |
| **Tavily** | 通用网络搜索,AI 优化结果 | [tavily.com](https://tavily.com) → 有免费额度 |
| **Exa** | 语义搜索,查找相似内容 | [exa.ai](https://exa.ai) → 有免费额度 |
| **Gemini** | 深度搜索模式,跨来源综合分析 | [ai.google.dev](https://ai.google.dev) → 有免费额度 |
| **AMiner** | 中文学术社区、学者画像 | [open.aminer.cn](https://open.aminer.cn) → 免费注册 |

**最低推荐配置:** Semantic Scholar(免费)+ arXiv(免费)+ Tavily 或 Exa 任选一个。

```bash
# 在 shell 配置文件(~/.zshrc 或 ~/.bashrc)中设置 API key
export TAVILY_API_KEY="tvly-..."
export EXA_API_KEY="..."
export GEMINI_API_KEY="..."     # 可选:深度搜索
export AMINER_API_KEY="..."     # 可选:中文学术搜索
```

### 社交媒体阅读(social-media-paper-triage 用)

| 平台 | 工具 | 安装方式 |
|------|------|---------|
| **任意 URL** | [Jina Reader](https://jina.ai/reader/) | 无需安装 - `curl https://r.jina.ai/URL` |
| **Twitter/X** | [xreach](https://github.com/xreach/xreach) | `npm i -g xreach` + 浏览器 cookie 认证 |
| **小红书/微博/微信** | [Agent Reach](https://github.com/Panniantong/Agent-Reach) | Docker + 各平台单独认证 |

**最低推荐配置:** Jina Reader(零配置,适用于大部分 URL)。

### Zotero(zotero-management 用)

1. 安装 [Zotero](https://www.zotero.org/download/)
2. 创建 API key:[zotero.org/settings/keys](https://www.zotero.org/settings/keys)
3. 获取 User ID:同一设置页面可查看

```bash
export ZOTERO_API_KEY="..."
export ZOTERO_USER_ID="..."
```

### 学术图表生成(academic-figure-generation 用)

需要 [PaperBanana](https://github.com/paperbanana/PaperBanana) 本地部署。详见 skill 的 SKILL.md。

### 出版商 TDM Keys (paper-fulltext-harvest 用)

所有 keys 都是可选的 — 仅需 `UNPAYWALL_EMAIL` 即可走 OA-only 模式。配置如下 key 以解锁付费内容的机构 TDM (Text and Data Mining) API 访问：

| Key | 解锁什么 | 如何获取 |
|-----|---------|---------|
| `ELSEVIER_API_KEY` + `ELSEVIER_INSTTOKEN` | Elsevier ScienceDirect 全文 XML | API key 免费注册 [dev.elsevier.com](https://dev.elsevier.com/)。Insttoken 需图书馆向 Elsevier 申请。 |
| `WILEY_TDM_TOKEN` | Wiley Online Library 全文 PDF | 图书馆需签署 [Wiley TDM 协议](https://onlinelibrary.wiley.com/library-info/resources/text-and-datamining)，token 发给一个机构联系人。 |
| `SPRINGER_API_KEY` | Springer Nature OpenAccess 全文 | 免费注册 [dev.springernature.com](https://dev.springernature.com/) |
| `UNPAYWALL_EMAIL` | 跨出版商的 OA PDF | 填写邮箱 |
| `CROSSREF_MAILTO`, `OPENALEX_MAILTO` | Crossref/OpenAlex polite-pool 限流提高 | 填写邮箱（推荐） |

对于没有 TDM 的付费出版商 (ACS、RSC、T&F、许多中文期刊)，skill 包含一个浏览器回退方案 — 通过 OpenClaw 的 `browser` 工具 + `profile="user"` 驱动用户已登录的 Chrome。

```bash
export ELSEVIER_API_KEY="..."
export ELSEVIER_INSTTOKEN="..."
export WILEY_TDM_TOKEN="..."
export UNPAYWALL_EMAIL="you@institution.edu"
```

**重要：** TDM API 要求请求从机构 IP 白名单发出 — 必须在机构网络或 VPN 上使用。

---

## 设计理念

**为什么做这个仓库:**

现有的「AI 科研工具」仓库(如 `claude-scientific-skills`)收录了数百个具体工具,大部分对具体研究者来说用不上,而且它们只描述工具*做什么*,不说*什么时候*、*为什么*要用。

这个仓库编码的是**科研方法论** -- 资深研究者经年累月内化的决策过程:

- *什么时候*该快速扫描 vs 深度阅读一篇论文
- *怎么*系统性地调研一个领域并找到自己的定位
- *哪个*搜索引擎适合什么类型的查询
- *怎么*从一个模糊的观察发展成具体的研究贡献

每个 skill 是一个工作流,不是一个函数调用。

**设计原则:**

1. **给 AI 看的,不是摆设** - Skill 内容是 agent 指令,不是人类文档
2. **高阶优于低阶** - 方法论优于工具调用
3. **模块化** - 按需选择
4. **跨平台** - 同一个 SKILL.md 格式兼容 OpenClaw、Claude Code、Codex 及任何 agent

---

## 贡献

这是一个持续演进的仓库。随着研究工作流的成熟,新 skill 会不断加入。

贡献新 skill:
1. 创建 `skills/<skill-name>/SKILL.md`
2. 参考现有 skills 的格式(YAML 头 + markdown 正文)
3. 重点写 *什么时候* 和 *为什么*,而不仅仅是 *怎么做*
4. 可选添加 `scripts/`、`references/` 或 `assets/` 目录
5. 提 PR 并附一段简短的工作流描述

## 许可证

MIT
