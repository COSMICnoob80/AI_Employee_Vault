# AEWACS TACTICAL BRIEF V3 — DOCUMENTATION-VERIFIED EDITION
## Claude Code × Antigravity: Dual-Tool Operations Manual for Gold Tier

**Classification:** VERIFIED — Every claim sourced from official documentation  
**Date:** 04 March 2026  
**Operator:** Shah G | **Callsign:** AEWACS  
**Mission:** Gold Tier Execution — Personal AI Employee Vault  

---

# PART I — CLAUDE CODE (Verified from code.claude.com/docs)

## 1. MEMORY SYSTEM

**Source:** code.claude.com/docs/en/memory

Claude Code has a hierarchical memory system loaded at EVERY session start:

| Priority | Type | Location | Shared With |
|----------|------|----------|-------------|
| 1 (Highest) | Enterprise Policy | Linux: `/etc/claude-code/CLAUDE.md` | All org users |
| 2 | Project Memory | `./CLAUDE.md` or `./.claude/CLAUDE.md` | Team via git |
| 3 | User Memory | `~/.claude/CLAUDE.md` | Just you (all projects) |
| 4 | Local Project | `./CLAUDE.local.md` | Just you (this project) |

**Key behaviors:**
- All files loaded into context automatically at session launch
- Higher hierarchy = higher precedence
- CLAUDE.local.md automatically added to .gitignore
- Claude Code recurses UP from cwd to root, reading any CLAUDE.md or CLAUDE.local.md it finds
- Nested CLAUDE.md in subtrees loaded only when Claude reads files in those subtrees

### @imports

CLAUDE.md files import additional files with `@path/to/import`:

```markdown
See @README for project overview
See @package.json for npm commands
@docs/git-instructions.md
@~/.claude/my-project-instructions.md  # Home dir imports work
```

- Both relative and absolute paths allowed
- NOT evaluated inside markdown code spans/blocks (avoids collisions)
- Recursive imports allowed, max-depth of 5 hops
- Run `/memory` to see what memory files are loaded

### # Shortcut (VERIFIED — THIS IS REAL)

The fastest way to add a memory: start your input with `#`:

```
# Always use descriptive variable names
```

You'll be prompted to select which memory file to store it in. This creates PERSISTENT memory loaded every future session.

### /memory Command

Opens any memory file in your system editor for extensive additions or organization.

### /init Command

Bootstrap a CLAUDE.md for your codebase. Analyzes project structure and creates starter file. If CLAUDE.md already exists, suggests improvements.

### .claude/rules/ Directory

**Source:** code.claude.com/docs/en/memory (How Claude remembers your project)

Organize rules in `.claude/rules/` with individual .md files:

```
your-project/
├── .claude/
│   ├── CLAUDE.md
│   └── rules/
│       ├── code-style.md
│       ├── testing.md
│       └── security.md
```

Rules can be scoped to specific files using YAML frontmatter:

```yaml
---
paths:
  - "src/api/**/*.ts"
---
# API Development Rules
- All API endpoints must include input validation
```

Rules WITHOUT paths are loaded unconditionally. Path-scoped rules trigger when Claude reads matching files.

### Auto Memory

Claude writes notes itself based on corrections/preferences. Separate from CLAUDE.md. Both loaded at session start.

### Best Practices for CLAUDE.md

**Source:** code.claude.com/docs/en/best-practices

- Target under 200 lines per CLAUDE.md file
- Be specific: "Use 2-space indentation" > "Format code properly"
- Format as bullet points under descriptive markdown headings
- Review periodically as project evolves
- If instructions growing large, split using imports or .claude/rules/

---

## 2. PLAN MODE (VERIFIED — BUILT-IN)

**Source:** code.claude.com/docs/en/common-workflows

Plan Mode = READ-ONLY state. Claude can explore, analyze, create plans but CANNOT modify files or run destructive commands.

### When to Use
- Multi-step implementation requiring edits to many files
- Code exploration before changing anything
- Interactive development — iterate on direction with Claude

### How to Activate

| Method | Command |
|--------|---------|
| During session | **Shift+Tab** twice (cycles: Normal → Auto-Accept → Plan) |
| New session | `claude --permission-mode plan` |
| Headless | `claude --permission-mode plan -p "Analyze auth system"` |
| Default config | `.claude/settings.json` → `{ "permissions": { "defaultMode": "plan" } }` |

### Plan Mode Indicators
- `⏵⏵ accept edits on` = Auto-Accept Mode
- `⏸ plan mode on` = Plan Mode

---

## 3. SLASH COMMANDS & SKILLS

**Source:** code.claude.com/docs/en/slash-commands, /skills, /common-workflows

### Built-In Commands

| Command | Purpose | When to Use |
|---------|---------|-------------|
| `/clear` | Wipe conversation, reload CLAUDE.md | Between unrelated tasks |
| `/compact` | Summarize conversation (lossy) | When >50% context used, same task |
| `/init` | Bootstrap CLAUDE.md | Once per project setup |
| `/memory` | Edit CLAUDE.md files | Add/edit persistent instructions |
| `/agents` | Manage custom subagents | Create, edit, view, delete subagents |
| `/resume` | Resume previous session (picker) | Return to earlier work |
| `/context` | Visualize context usage | Check token consumption |
| `/cost` | Show token usage | Monitor spending |
| `/model` | Switch AI model | Change between Sonnet/Opus/Haiku |
| `/help` | List available commands | Discover features |
| `/sandbox` | Enable sandboxed bash | Security isolation |
| `/rewind` | Restore previous state | Undo/rollback |
| `/login` | Switch accounts | Change auth |
| `/permissions` | Manage permissions | Allowlist domains, commands |
| `/review` | Request code review | Post-implementation review |
| `/feedback` | Send feedback to Anthropic | Report issues |
| `/teleport` | Pull web session to terminal | Remote → local handoff |

### /clear vs /compact Decision

- **/clear**: Different task entirely. Context cluttered with failed approaches. Corrected Claude 2+ times on same issue.
- **/compact**: Same task continues. Need more room. Specify focus: `/compact Focus on: [current task]`

### Skills System (Replaces Custom Commands)

**Source:** code.claude.com/docs/en/skills

Skills are the CURRENT way to create custom slash commands. `.claude/commands/` still works but Skills are recommended.

**Structure:**

```
.claude/skills/
└── my-skill/
    ├── SKILL.md          # Required: YAML frontmatter + instructions
    ├── scripts/           # Optional: executable scripts
    ├── references/        # Optional: templates, docs
    └── examples/          # Optional: example outputs
```

**SKILL.md format:**

```yaml
---
name: verify-task
description: Runs verification protocol for vault components. Use after completing any S-task or G-task.
---

When verifying a component:
1. Read the relevant skill documentation
2. Check all files exist
3. Run test scripts with --dry-run
4. Update VERIFICATION_REPORT.md
```

**Scopes:**
- Personal: `~/.claude/skills/` (all projects)
- Project: `.claude/skills/` (this project, shared via git)

**Key fields:**
- `disable-model-invocation: true` → Only YOU can invoke (for deploy, send, etc.)
- `user-invocable: false` → Only Claude can invoke (background knowledge)
- `allowed-tools` → Restrict which tools the skill can use
- SKILL.md under 500 lines, move reference material to separate files

**Budget:** Skill descriptions loaded into context at 2% of context window (~16,000 chars fallback). Run `/context` to check.

---

## 4. SUBAGENTS

**Source:** code.claude.com/docs/en/sub-agents

### Built-In Subagents (Always Available)

| Subagent | Model | Tools | Mode | Purpose |
|----------|-------|-------|------|---------|
| General-purpose | Sonnet | ALL tools | Read + Write | Complex multi-step tasks |
| Plan | Sonnet | Read, Glob, Grep, Bash | Read-only | Research during Plan Mode |
| Explore | Haiku | Glob, Grep, Read, Bash (read-only) | Read-only | Fast codebase exploration |

**Explore thoroughness levels:** Quick → Medium → Very thorough

### Custom Subagents

**Locations:**

| Type | Path | Scope | Priority |
|------|------|-------|----------|
| Project | `.claude/agents/` | Current project | Highest |
| User | `~/.claude/agents/` | All projects | Lower |

**File format:** Markdown with YAML frontmatter:

```yaml
---
name: vault-verifier
description: Verification specialist for AI Employee Vault components. Use proactively after any task completion.
tools: Read, Grep, Glob, Bash
model: inherit
permissionMode: default
skills: verify-task
---

You are a verification specialist for the AI Employee Vault...
```

**Configuration fields:**
- `name` (required): lowercase + hyphens identifier
- `description` (required): when to use — include "use PROACTIVELY" for auto-delegation
- `tools` (optional): comma-separated. If omitted, inherits ALL tools including MCP
- `model` (optional): `sonnet`, `opus`, `haiku`, or `inherit` (match main session)
- `permissionMode` (optional): `default`, `acceptEdits`, `bypassPermissions`, `plan`, `ignore`
- `skills` (optional): auto-load skills when subagent starts

**Critical rules:**
- Subagents CANNOT spawn other subagents (no infinite nesting)
- Own context window (don't pollute main conversation)
- Project agents override user agents on name conflict
- Resumable: each execution gets unique agentId, can resume with full context

### Managing Subagents

- `/agents` → Interactive menu (recommended — shows all tools, creation wizard)
- Direct file management → Create .md files in agents directories

---

## 5. BEST PRACTICES

**Source:** code.claude.com/docs/en/best-practices

### The #1 Constraint: Context Window

> "Claude's context window holds your entire conversation. It fills up fast. LLM performance degrades as context fills."

**Management strategies:**
- Track with `/context` or custom status line
- `/clear` between unrelated tasks
- `/compact` when >50% used on same task
- Include tests/screenshots so Claude can self-verify
- Reference files with `@` instead of describing locations
- Let Claude fetch what it needs (Bash, MCP, file reading)

### Feedback Loop Pattern

1. **Esc**: Stop Claude mid-action (context preserved, redirect)
2. **Esc + Esc** or **/rewind**: Restore previous state
3. **Interrupt**: Type correction mid-generation, press Enter
4. **/clear**: If corrected 2+ times on same issue, start fresh with better prompt

> "A clean session with a better prompt almost always outperforms a long session with accumulated corrections."

### Agentic Loop

Claude works in three phases: **Gather context → Take action → Verify results**. These blend together. Claude chains dozens of actions, course-correcting along the way. You're part of this loop — interrupt to steer anytime.

---

## 6. CLI FLAGS (Key Ones)

**Source:** code.claude.com/docs/en/cli-reference

| Flag | Purpose |
|------|---------|
| `--continue` | Resume most recent conversation |
| `--resume` | Session picker |
| `--permission-mode plan` | Start in Plan Mode |
| `-p "prompt"` | Headless/non-interactive mode |
| `--output-format json` | Structured output |
| `--agents '{...}'` | Dynamic CLI subagents |
| `--append-system-prompt "..."` | Add instructions keeping defaults |
| `--allowedTools "..."` | Pre-approve specific tools |
| `--remote` | Run on cloud (web session) |
| `--add-dir /path` | Add extra directory to context |

### Parallel Execution

```bash
claude --remote "Fix auth test"
claude --remote "Update API docs"  
claude --remote "Refactor logger"
```

Monitor all with `/tasks`. Teleport to terminal with `/teleport`.

---

# PART II — GOOGLE ANTIGRAVITY (Verified from Codelabs + Official Blog + Guides)

## 1. CORE ARCHITECTURE

**Source:** codelabs.developers.google.com/getting-started-google-antigravity, developers.googleblog.com

Antigravity = Agent-first IDE (forked from VS Code). NOT a chatbot with sidebar. Your role shifts from writer to architect/orchestrator.

### Two Primary Surfaces

| Surface | Purpose | Key Action |
|---------|---------|------------|
| **Agent Manager** | Mission Control — spawn, monitor, orchestrate multiple agents asynchronously | High-level task dispatch |
| **Editor** | VS Code-like — syntax highlighting, file explorer, terminal, inline AI | Hands-on coding |

Toggle between them: **Cmd + E** or buttons in top-right corner.

### Agent Manager Components

1. **Inbox** — Track all conversations in one place. Return to previous tasks.
2. **Start Conversation** — Begin new agent task
3. **Workspaces** — Multiple project directories. Add/switch anytime.
4. **Playground** — Scratch area. Start conversation, optionally convert to workspace.
5. **Editor View** — Switch to hands-on editing
6. **Browser** — Chrome integration with browser subagent

### Editor Features

- **Auto-complete** with tab
- **Tab to import** for missing dependencies
- **Tab to jump** to next logical cursor position
- **Cmd + I** for inline commands (editor + terminal)
- **Cmd + L** toggle agent side panel
- **@ mentions** for files, directories, MCP servers
- **/ commands** for workflows
- **Explain and fix** on hover over problems
- **Send problems to agent** from Problems panel
- **Send terminal output** to agent with Cmd + L

---

## 2. AGENT MODES & POLICIES

**Source:** codelabs.developers.google.com/getting-started-google-antigravity

### Agent Modes

| Mode | Behavior | Use When |
|------|----------|----------|
| **Planning** | Agent plans before executing. Creates task groups, artifacts. More output. Higher quality. | Complex tasks, deep research, collaborative work |
| **Fast** | Agent executes directly. Minimal planning. | Renaming variables, quick bash commands, simple tasks |

### Terminal Execution Policy

| Setting | Behavior |
|---------|----------|
| **Always proceed** | Auto-execute (except deny list) |
| **Request review** | User must approve each command |

### Review Policy (for Artifacts)

| Setting | Behavior |
|---------|----------|
| **Always Proceed** | Agent never asks for review |
| **Agent Decides** | Agent chooses when to ask |
| **Request Review** | Agent always asks |

### JavaScript Execution Policy

| Setting | Behavior |
|---------|----------|
| **Always Proceed** | Full browser autonomy (highest risk) |
| **Request review** | Permission needed for JS execution |
| **Disabled** | No JS execution in browser |

### Preset Configurations

| Preset | Description | Recommended? |
|--------|-------------|--------------|
| **Secure Mode** | Maximum restrictions | For sensitive environments |
| **Review-driven** | Agent asks frequently | ✅ RECOMMENDED — good balance |
| **Agent-driven** | Full autonomy, never asks | For greenfield/clear tasks |
| **Custom** | Configure each policy individually | Advanced users |

---

## 3. ARTIFACTS — THE TRUST LAYER

**Source:** codelabs.developers.google.com/getting-started-google-antigravity (Section 5)

Artifacts solve the "Trust Gap." When agent claims "I fixed the bug," artifacts prove it.

### Artifact Types

| Type | When Created | Purpose |
|------|-------------|---------|
| **Task List** | Before coding | Structured plan of steps. Review, add comments to change. |
| **Implementation Plan** | Before coding | Architecture of changes, tech stack, high-level description. REVIEWABLE. |
| **Walkthrough** | After coding | Summary of changes + how to test. May include screenshots/recordings. |
| **Code Diffs** | During coding | Review changes, accept/reject, add comments. |
| **Screenshots** | During/after | UI state before and after changes |
| **Browser Recordings** | During browser testing | Video of agent's browser session for verification |

### Feedback on Artifacts

- **Google Docs-style comments** — Select, comment, submit
- Agent incorporates feedback mid-run without stopping
- Comments trigger plan updates → code updates → new walkthrough
- **Undo changes** available after each step: ↩️ "Undo changes up to this point"

### Planning Mode Workflow

1. Ensure **Planning** mode (not Fast)
2. Give task prompt
3. Agent creates **Implementation Plan** → Review, comment (e.g., "use FastAPI not Flask")
4. Agent creates **Task List** → Review, add verification instructions
5. Agent generates code → **Accept all / Reject all / Review changes**
6. Agent starts server, tests in browser → Creates **Walkthrough** with screenshots/recordings
7. Comment on walkthrough for iterations

**Pro tips from docs:**
- Always submit comments (triggers agent update)
- If agent codes before you confirm plans, comment on plans/tasks and resubmit
- Can stop coding task, add comments to plans, try again

---

## 4. RULES & WORKFLOWS

**Source:** codelabs.developers.google.com/getting-started-google-antigravity (Section 9)

### Rules = System Instructions (Always Active)

Guidelines the agent follows while generating code/tests.

**Locations:**
- Global: `~/.gemini/GEMINI.md`
- Workspace: `<workspace>/.agent/rules/`

**Access:** Editor → `...` menu (top-right) → Customizations → Rules

**Example:**

```markdown
# code-style-guide
* Make sure all code is styled with PEP 8
* Make sure all code is properly commented
```

### Workflows = Saved Prompts (Triggered with /)

On-demand prompts you trigger manually.

**Locations:**
- Global: `~/.gemini/antigravity/global_workflows/`
- Workspace: `<workspace>/.agent/workflows/`

**Access:** Editor → `...` → Customizations → Workflows

**Example:**

```markdown
# generate-unit-tests
* Generate unit tests for each file and each method
* Make sure unit tests are named with test_ prefix
```

**Usage:** Type `/generate` in chat → select workflow → Enter

### Analogy
> Rules = CLAUDE.md (always loaded) | Workflows = Custom slash commands (user-triggered)

---

## 5. SKILLS — PROGRESSIVE DISCLOSURE

**Source:** codelabs.developers.google.com/getting-started-google-antigravity (Section 10)

Skills = specialized knowledge packages that sit DORMANT until needed. Loaded into context ONLY when your request matches the skill's description. Solves "tool bloat."

### Scopes

| Scope | Location | Availability |
|-------|----------|-------------|
| Global | `~/.gemini/antigravity/skills/` | All projects |
| Workspace | `<workspace>/.agent/skills/` | This project only |

### Skill Structure

```
my-skill/
├── SKILL.md      # REQUIRED: metadata + instructions
├── scripts/       # Optional: Python/Bash for execution
├── references/    # Optional: text, docs, templates
└── assets/        # Optional: images, logos
```

### SKILL.md Format

```yaml
---
name: code-review
description: Reviews code changes for bugs, style issues, and best practices. Use when reviewing PRs or checking code quality.
---

# Code Review Skill

When reviewing code, follow these steps:
## Review checklist
1. Correctness
2. Edge cases
3. Style
4. Performance
```

### How Skills Work

1. Agent reads ONLY metadata (name + description) for all configured skills at launch
2. When request matches a skill's description → agent loads full SKILL.md instructions
3. Agent follows instructions from the skill
4. Resources/scripts referenced from SKILL.md loaded only when needed

---

## 6. BROWSER SUBAGENT

**Source:** codelabs.developers.google.com, docs referenced within

The browser subagent is a SEPARATE model specialized for browser interaction, different from main agent model.

**Capabilities:**
- Click, scroll, type, navigate
- Read pages via DOM capture, screenshots, or markdown parsing
- Take videos (browser recordings)
- Read console logs
- Operate within Antigravity-managed Chrome browser

**Setup:**
1. Requires Antigravity browser extension (Chrome)
2. First use triggers setup prompt
3. Install extension from Chrome Web Store
4. Agent requests permission for browser actions

**Use cases for your project:**
- Test LinkedIn poster → verify post appeared
- Screenshot evidence for verification
- E2E testing of web-based components

---

## 7. SECURITY

**Source:** codelabs.developers.google.com (Section 11)

### Terminal Command Policies

| Policy | Behavior |
|--------|----------|
| **Off** | Never auto-execute (use Allow List for exceptions) |
| **Auto** | Agent decides based on safety models |
| **Turbo** | Always execute (use Deny List for restrictions) |

### Allow List (with Off policy)
- Positive security model: everything forbidden unless permitted
- Add specific commands: `ls -al`, `python`, `npm test`
- Most secure configuration

### Deny List (with Turbo policy)
- Negative security model: everything allowed unless forbidden
- Block dangerous commands: `rm`, `sudo`, `curl`, `wget`

### Browser Security
- **Browser URL Allowlist**: `~/.gemini/antigravity/browserAllowlist.txt`
- Add only trusted domains

---

## 8. MCP IN ANTIGRAVITY

**Source:** Multiple verified guides

**Config location:** `~/.gemini/antigravity/mcp_config.json`

```json
{
  "mcpServers": {
    "my-server": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": { "GITHUB_TOKEN": "ghp_..." }
    }
  }
}
```

**Access:** Agent pane → `...` menu → MCP Servers → Manage MCP Servers → View raw config

**MCP Store:** Built-in marketplace for installing MCP connectors (Sequential Thinking, GitHub, databases, etc.)

---

## 9. CONFIGURATION FILES COMPARISON

| Concept | Claude Code | Antigravity |
|---------|------------|-------------|
| System instructions | CLAUDE.md | GEMINI.md + Rules |
| Per-project rules | .claude/rules/ | .agent/rules/ |
| Saved prompts | .claude/skills/ (SKILL.md) | .agent/workflows/ |
| Progressive knowledge | Skills (.claude/skills/) | Skills (.agent/skills/) |
| Custom agents | .claude/agents/ | Not yet supported natively |
| MCP config | settings.json / .mcp.json | mcp_config.json |
| User-level config | ~/.claude/ | ~/.gemini/ |

---

# PART III — DUAL-TOOL SYNERGY FOR YOUR VAULT

## Division of Labor

| Task | Tool | Why |
|------|------|-----|
| **Planning** | Claude Code (Plan Mode) | Reads vault files, @imports, creates detailed plans |
| **Implementation** | Claude Code | Direct file access, MCP servers, bash execution |
| **Parallel verification** | Antigravity (Agent Manager) | Multiple agents simultaneously, artifacts as evidence |
| **Browser testing** | Antigravity (Browser Subagent) | LinkedIn posting, web UI testing, screenshot/video proof |
| **Code review** | Either | Claude Code has /review; Antigravity has inline comments |
| **Documentation** | Claude Code | Direct file editing, CLAUDE.md updates |

## Corrected Session Protocol

### Starting a Session (Claude Code)

```
# 1. Clear previous context
/clear

# 2. Enter Plan Mode for orientation
[Press Shift+Tab twice → "⏸ plan mode on"]

# 3. Read current state
Read @Dashboard.md @VERIFICATION_REPORT.md @SPEC.md — what's current state and what's next?

# 4. Review plan output, then exit Plan Mode
[Press Shift+Tab → back to Normal]

# 5. Give execution instruction
Implement G1: Weekly CEO Briefing generator per SPEC.md requirements
```

### Between Tasks
```
/clear
```

### Long Sessions (Same Task)
```
/cost              # Check token usage
/context           # Check context usage
/compact Focus on: [current G-task specifics]
```

### End of Session
```
# Save learnings as persistent memory
# Update Dashboard.md and VERIFICATION_REPORT.md
# Commit changes
```

### Verification (Antigravity)

1. Open AI Employee Vault as workspace
2. Create verification task in Agent Manager:
   > "Verify G1 CEO Briefing generator: check all files exist per SPEC.md, run test with --dry-run, verify output format"
3. Agent creates Task List + Implementation Plan artifacts
4. Review artifacts for completeness
5. If browser testing needed (LinkedIn, etc.), agent invokes browser subagent
6. Screenshots + recordings saved as verification evidence

---

# PART IV — GOLD TIER BATTLE PLAN

## Requirements (Hackathon Doc)
1. All Silver ✅ (COMPLETE)
2. Full cross-domain integration (Personal + Business)
3. Odoo accounting integration via MCP
4. Facebook, Instagram, Twitter integration
5. Multiple MCP servers
6. Weekly CEO Briefing generation
7. Error recovery, audit logging
8. Ralph Wiggum loop (persistent task completion)

## Prioritized Attack Sequence

### Wave 1: Zero External Dependencies (Ship First)

**G1: Weekly CEO Briefing Generator** (3-4 hrs)
- Aggregates data from all domains (Gmail, Calendar, LinkedIn, tasks)
- Generates markdown report
- Create as Claude Code skill: `.claude/skills/ceo-briefing/SKILL.md`
- Test with `--dry-run` using mock data

**G2: Error Recovery + Audit Logging** (3-4 hrs)
- Try/except wrappers on all watchers
- JSON audit log: `Logs/audit.jsonl`
- Recovery procedures for each component
- Skill: `.claude/skills/audit-check/SKILL.md`

**G3: Ralph Wiggum Stop Hook** (2-3 hrs)
- Persistent task completion loop
- Check task queue → execute → verify → report
- Uses Claude Code hooks system for pre/post actions

### Wave 2: Build on Completed Work

**G4: Additional MCP Servers** (3-4 hrs)
- Add 2-3 more MCP servers beyond Gmail Send
- Calendar MCP, File System MCP, or custom
- Register in vault's MCP config

**G5: Cross-Domain Integration** (4-6 hrs)
- Personal + Business domain bridging
- CEO Briefing pulls from all domains
- Unified dashboard updates

### Wave 3: External API Dependent

**G6: Odoo Community Integration** (6-8 hrs)
- Requires Odoo instance setup
- MCP server for Odoo XML-RPC API
- Accounting data flow

**G7: Social Media (FB/IG/Twitter)** (4-6 hrs)
- API keys or Playwright automation
- Posting pipeline similar to LinkedIn S3
- Cross-platform content adaptation

## Anti-Hamster-Wheel Protocol

1. `/clear` at every task boundary
2. Plan Mode BEFORE execution (Shift+Tab twice)
3. `#` to save learnings permanently after discoveries
4. `@files` instead of re-explaining context
5. Skills for repeated workflows
6. Vault is the memory — not chat history
7. Ship imperfect → verify with Antigravity → iterate
8. If corrected Claude 2+ times: `/clear` + better prompt
9. Check `/cost` and `/context` every 20-30 min

---

# PART V — IMMEDIATE NEXT ACTIONS FOR GOLD TIER

## Step 1: Setup (Do This First — 30 min)

In Claude Code, at `~/AI_Employee_Vault/`:

### A. Create /start Skill

```bash
mkdir -p .claude/skills/start
```

Create `.claude/skills/start/SKILL.md`:

```yaml
---
name: start
description: Session initialization protocol. Use at the beginning of every work session.
disable-model-invocation: true
---

Session Start Protocol:
1. Read @SPEC.md for architecture
2. Read @Dashboard.md for current status  
3. Read @VERIFICATION_REPORT.md for progress
4. Report: what's complete, what's next, any blockers
5. Suggest the next task to tackle
```

### B. Create /verify Skill

```yaml
---
name: verify
description: Verification protocol for vault components. Use after completing any task.
disable-model-invocation: true
allowed-tools: Read, Grep, Glob, Bash
---

Verification Protocol:
1. Read SPEC.md requirement for the completed task
2. Check all required files exist
3. Verify file contents match spec
4. Run any test scripts with --dry-run
5. Update VERIFICATION_REPORT.md with results
6. Update Dashboard.md with new status
```

### C. Create Verifier Subagent

Create `.claude/agents/verifier.md`:

```yaml
---
name: verifier
description: Verification specialist. Use PROACTIVELY after any task completion to verify against SPEC.md.
tools: Read, Grep, Glob, Bash
model: sonnet
---

You are the verification agent for the AI Employee Vault.
Your job: verify completed work against SPEC.md requirements.
Never modify production files. Only read, check, and report.
Update VERIFICATION_REPORT.md with pass/fail results.
```

### D. Add Persistent Memories

```
# Always update VERIFICATION_REPORT.md after completing vault tasks
# Python watchers use watchdog library with OAuth2 for Gmail
# Skills documentation follows 7-section format
# MCP servers use FastMCP framework
# Test all scripts with --dry-run before live execution
# Silver tier 100% complete. Working on Gold tier.
```

### E. Update Project CLAUDE.md

Add @imports:

```markdown
@SPEC.md
@VERIFICATION_REPORT.md
@Dashboard.md
```

## Step 2: Fix S3 Cosmetic Issues (5 min)

- SPEC.md: Update skill count from 7 → 8
- schedule_watchers.sh: Fix incorrect path comment

## Step 3: Begin G1 — CEO Briefing Generator

```
/clear
[Shift+Tab twice → Plan Mode]
Read @SPEC.md lines 152-165 for Gold tier requirements. Plan the Weekly CEO Briefing generator. It should aggregate data from Gmail, Calendar, LinkedIn activity, and task status into a comprehensive markdown report.
[Review plan → Shift+Tab → Normal mode]
Execute the plan.
```

---

# QUICK REFERENCE CARD

## Claude Code Essentials

| Action | Command |
|--------|---------|
| Reset context | `/clear` |
| Compress context | `/compact Focus: [task]` |
| Plan mode ON | Shift+Tab twice |
| Plan mode OFF | Shift+Tab |
| Save memory | `# your learning here` |
| Edit memory | `/memory` |
| Check context | `/context` |
| Check cost | `/cost` |
| Resume session | `claude --continue` or `claude --resume` |
| Reference file | `@path/to/file` |
| Custom skill | `.claude/skills/name/SKILL.md` |
| Custom agent | `.claude/agents/name.md` |
| Bootstrap | `/init` |

## Antigravity Essentials

| Action | How |
|--------|-----|
| Toggle Editor/Manager | Cmd + E |
| Toggle agent panel | Cmd + L |
| Inline command | Cmd + I |
| Start workflow | Type `/` in chat |
| Add context | Type `@` in chat |
| Global rules | `~/.gemini/GEMINI.md` |
| Workspace rules | `.agent/rules/` |
| Workflows | `.agent/workflows/` |
| Skills | `.agent/skills/` |
| MCP config | `~/.gemini/antigravity/mcp_config.json` |
| Browser allowlist | `~/.gemini/antigravity/browserAllowlist.txt` |

---

*Brief compiled from verified official documentation. Zero hallucination tolerance.*
*Sources: code.claude.com/docs/en/*, codelabs.developers.google.com, developers.googleblog.com*
