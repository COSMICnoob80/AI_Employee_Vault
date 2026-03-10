# CEO Briefing Generator

Generate a weekly executive status report aggregating all vault data.

## Triggers
- "generate a CEO briefing"
- "weekly status report"
- "CEO briefing"
- "executive summary"
- "weekly report"

## Instructions

When the user asks for a CEO briefing or weekly status report:

1. **Default run** — generate the current week's briefing:
   ```bash
   python3 ~/AI_Employee_Vault/Scripts/ceo_briefing.py
   ```

2. **Dry run** — preview without writing files:
   ```bash
   python3 ~/AI_Employee_Vault/Scripts/ceo_briefing.py --dry-run
   ```

3. **Specific week** — target a past week:
   ```bash
   python3 ~/AI_Employee_Vault/Scripts/ceo_briefing.py --week YYYY-WNN
   ```

4. **Custom output** — write to a specific path:
   ```bash
   python3 ~/AI_Employee_Vault/Scripts/ceo_briefing.py --output PATH
   ```

After running, read the generated report and present a concise summary of key findings to the user, highlighting any action items that need attention.

The report is saved to `Reports/CEO_Briefing_YYYY-MM-DD.md` by default.

## Notes
- Report generation is autonomous per Company_Handbook — no approval needed
- Reports/ directory is gitignored (generated output)
- All vault reads are read-only
