# Approval Requester Skill

## Description
Determines when AI Employee actions require human approval before execution. Acts as a safety gate in the automation pipeline, routing sensitive actions through the Pending_Approval folder for human review. Helps maintain trust and control by enforcing threshold rules and risk assessment.

## Capabilities
- Classify actions into approval-required vs autonomous
- Apply threshold rules (financial, communication, data, public)
- Generate structured approval request files with YAML frontmatter
- Assess risk level (low/medium/high/critical)
- Provide human-readable action summaries
- Track approval status through the pipeline

## Input Format
```
Action: [description of action to perform]
Type: [email_send | financial | social_media | data_deletion | system_change]
Value: [monetary value if applicable, else "N/A"]
Target: [recipient/destination]
```

## Output Format
```
Requires Approval: [Yes | No]
Category: [External Communication | Financial | Public Posting | Data Modification]
Risk Level: [Low | Medium | High | Critical]
Reason: [Brief explanation of why approval is needed]
```

## Rules

### Category: External Communication
1. Any email to external recipients
2. Any message to clients, vendors, partners
3. Automated replies to unknown senders
4. Newsletter or bulk communications
5. Exception: internal notes and drafts (no approval needed)

### Category: Financial (Threshold: >500 PKR)
1. Any purchase, subscription, or payment >500 PKR
2. Recurring charges or subscription sign-ups
3. Refund processing or financial adjustments
4. Invoice approval or payment authorization
5. Exception: reporting/tracking existing transactions (no approval needed)

### Category: Public Posting
1. Any social media post (Twitter, LinkedIn, Facebook, etc.)
2. Blog posts or website content changes
3. Public-facing documentation updates
4. Press releases or public statements
5. Exception: internal documentation (no approval needed)

### Category: Data Modification
1. Deleting files or records permanently
2. Modifying database records
3. Archiving or purging old data
4. Changing access permissions or credentials
5. Exception: creating new files in Inbox/Needs_Action (no approval needed)

## Examples

### Example 1: Email Send (Requires Approval)
**Input:**
```
Action: Send follow-up email to client about project timeline
Type: email_send
Value: N/A
Target: client@external-company.com
```

**Output:**
```
Requires Approval: Yes
Category: External Communication
Risk Level: Medium
Reason: Outbound email to external client. All external communications require human review before sending.
```

---

### Example 2: Small Purchase (No Approval Needed)
**Input:**
```
Action: Purchase office supplies from online store
Type: financial
Value: 350 PKR
Target: supplies-vendor.pk
```

**Output:**
```
Requires Approval: No
Category: Financial
Risk Level: Low
Reason: Purchase amount (350 PKR) is below the 500 PKR approval threshold. Proceeding autonomously.
```

---

### Example 3: Social Media Post (Requires Approval)
**Input:**
```
Action: Post project milestone announcement on LinkedIn
Type: social_media
Value: N/A
Target: LinkedIn company page
```

**Output:**
```
Requires Approval: Yes
Category: Public Posting
Risk Level: High
Reason: Public-facing content on social media. All posts representing the business require human approval before publishing.
```

---

### Example 4: Data Deletion (Requires Approval)
**Input:**
```
Action: Delete archived client records older than 2 years
Type: data_deletion
Value: N/A
Target: Archive/client_records/
```

**Output:**
```
Requires Approval: Yes
Category: Data Modification
Risk Level: Critical
Reason: Permanent deletion of client records. All irreversible data operations require explicit human authorization.
```

---

## Integration

- Route approval requests to [[Dashboard]] Approval Status
- Check thresholds against [[Company_Handbook]] rules
- Log all decisions in Logs/approval.log
