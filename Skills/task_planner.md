# Task Planner Skill

## Description
Analyzes tasks in /Needs_Action and creates actionable plans in /Plans. Parses YAML frontmatter to determine task type, priority, and generates step-by-step execution plans.

## Capabilities
- Parse task files (email, file_drop, manual)
- Identify required actions based on content analysis
- Estimate time/effort per task type
- Assign and inherit priority from source tasks
- Create step-by-step plans with checkboxes
- Link plans bidirectionally with source tasks via wikilinks

## Input Format
Task file from /Needs_Action with YAML frontmatter containing:
```yaml
type: [email|file_drop|manual]
priority: [urgent|high|normal|low]
status: pending
```

## Output Format
Plan file in /Plans/PLAN_[original_name].md with:
- YAML frontmatter referencing source task
- Numbered action steps with checkboxes
- Estimated completion time
- Dependencies (if any)
- Success criteria

## Planning Rules
1. High/urgent priority → Plan within same day, flag on [[Dashboard]]
2. Emails requiring response → Include draft response step
3. File drops → Include processing + categorization + archival steps
4. Multi-step tasks → Break into max 5 steps
5. Always include verification step at end

## Time Estimation by Type

| Task Type | Context | Estimated Time |
|-----------|---------|----------------|
| email | Response needed | 20 min |
| email | FYI / informational | 5 min |
| email | Financial (invoice/payment) | 15 min |
| file_drop | Standard processing | 15 min |
| manual | Simple task | 15 min |
| manual | Complex task | 60 min |

## Plan Template

```yaml
---
type: plan
source_task: "[path to original]"
created: [ISO timestamp]
estimated_time: [minutes]
priority: [inherited from task]
status: active
---
```

```markdown
# Plan: [Task Title]

## Source
[[original_task_file]]

## Steps
- [ ] Step 1: [Action]
- [ ] Step 2: [Action]
- [ ] Step 3: [Action]
- [ ] Verify: [Success criteria]

## Notes
[Any additional context]

## On Completion
- Move source task to /Done
- Update [[Dashboard]]
```

## Examples

### Example 1: Email requiring response
**Input**: Email from client about payment failure
**Plan**:
- [ ] Review email content and payment details
- [ ] Check [[Business_Goals]] for related subscription info
- [ ] Draft response to sender
- [ ] Send response (requires approval per [[Company_Handbook]])
- [ ] Verify: Payment status resolved, email archived

### Example 2: File drop
**Input**: New file in Inbox
**Plan**:
- [ ] Read and understand file content
- [ ] Categorize using [[email_classifier]] if applicable
- [ ] Take required action or delegate
- [ ] Archive to /Done with completion note
- [ ] Verify: File processed, Dashboard updated

### Example 3: Informational email
**Input**: Newsletter or FYI email
**Plan**:
- [ ] Scan content for actionable items
- [ ] Extract relevant info to [[Business_Goals]] if financial
- [ ] Archive after review
- [ ] Verify: No pending actions remain

## Integration
- Source tasks from [[Dashboard]] Active Tasks
- Financial items route to [[Business_Goals]]
- Follow [[Company_Handbook]] approval rules for external actions
- Use [[email_classifier]] for email categorization
