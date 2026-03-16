# Skills Index

All documented capabilities of the AI Employee system.

| Skill | File | Description |
|-------|------|-------------|
| Email Classifier | [[email_classifier]] | Categorizes emails by urgency/type and suggests actions |
| Gmail Processor | [[gmail_processor]] | Processes Gmail emails with response templates and escalation |
| Inbox Processor | [[inbox_processor]] | Monitors Inbox/ folder and creates task files from file drops |
| Approval Requester | [[approval_requester]] | Safety gate for actions requiring human approval |
| Task Planner | [[task_planner]] | Generates step-by-step plans from task files |
| Scheduler | [[scheduler]] | Automated watcher startup, self-healing, and cron management |
| MCP Gmail Send | [[mcp_gmail_send]] | MCP server exposing send_email tool via Gmail API |
| LinkedIn Poster | [[linkedin_poster]] | Automated LinkedIn text posting via Playwright |
| CEO Briefing | [[ceo_briefing]] | Aggregates vault data into weekly executive status report |
| Ralph Wiggum | [[ralph_wiggum]] | Autonomous task execution loop with priority queue and approval routing |
| MCP Vault FS | [[mcp_vault_fs]] | MCP server for safe vault file operations with path validation |
| MCP Vault Calendar | [[mcp_vault_calendar]] | MCP server for Google Calendar operations via OAuth2 |
| Cross-Domain Integration | [[cross_domain_integration]] | Unified view across personal and business domains with routing |
| Odoo Accounting | [[odoo_accounting]] | MCP server for Odoo Community accounting via JSON-RPC |
| Social Media Poster | [[social_media_poster]] | Automated posting to FB/IG/Twitter via Playwright with MCP server |

## Standard Skill Format

Every skill document follows the 7-section format:

1. **Description** — What the skill does
2. **Capabilities** — Specific abilities
3. **Input Format** — Expected input structure
4. **Output Format** — What it produces
5. **Rules** — Decision logic and constraints
6. **Examples** — Input/Output pairs demonstrating behavior
7. **Integration** — Links to other vault components
