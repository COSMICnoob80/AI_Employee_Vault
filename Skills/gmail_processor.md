# Gmail Processor Skill

## Description
Classify incoming emails, suggest responses, and determine escalation paths. Works with [[gmail_watcher.py|Gmail Watcher]] to process email tasks in Needs_Action.

## Capabilities
- Classify emails into: Urgent, Business, Personal, Spam
- Identify action type and priority level
- Suggest response templates
- Determine escalation requirements
- Track email threads and conversations

## Input Format
```
From: [sender email]
Subject: [subject line]
Body: [email content]
Keywords Matched: [list from watcher]
```

## Output Format
```
Category: [Urgent | Business | Personal | Spam]
Priority: [1-10]
Action: [specific action]
Response Template: [if applicable]
Escalate: [yes/no + reason]
```

## Classification Rules

### Category: Urgent (Priority 8-10)
1. Keywords: urgent, asap, critical, immediate, deadline today
2. From: known VIPs, boss, key clients
3. Contains: final notice, overdue, action required immediately
4. Thread: already replied but no response

### Category: Business (Priority 4-7)
1. Keywords: invoice, payment, meeting, project, proposal
2. From: work domain, vendors, partners
3. Contains: review request, approval needed, follow-up
4. Standard business correspondence

### Category: Personal (Priority 3-5)
1. From: known personal contacts, friends, family
2. Contains: personal topics, social events, greetings
3. Non-commercial, non-promotional

### Category: Spam (Priority 1-2)
1. Unknown sender with generic greeting
2. Promotional: sale, discount, limited offer
3. Contains: unsubscribe, suspicious links
4. Mass-mailing indicators

## Response Templates

### Template: Acknowledgment
```
Hi [Name],

Thank you for your email. I've received your message regarding [subject] and will review it shortly.

I'll get back to you by [timeframe].

Best regards
```

### Template: Request for Info
```
Hi [Name],

Thank you for reaching out. To help you better, I need some additional information:

1. [Question 1]
2. [Question 2]

Please reply with these details at your earliest convenience.

Best regards
```

### Template: Meeting Confirmation
```
Hi [Name],

Confirmed for [date/time]. Looking forward to it.

Meeting details:
- Date: [date]
- Time: [time]
- Location/Link: [details]

Best regards
```

### Template: Delay Notice
```
Hi [Name],

Thank you for your patience. I'm currently [reason] and will respond to your [subject] request by [new date].

If this is urgent, please [alternative contact method].

Best regards
```

## Examples

### Example 1: Urgent (Client Payment Failure)
**Input:**
```
From: cfo@bigclient.com
Subject: CRITICAL: Payment processing failed - invoice #8821
Body: Our payment gateway rejected the charge for invoice #8821 ($12,500). This is blocking our Q1 close. We need this resolved immediately or we'll have to escalate to your management. Please advise ASAP.
Keywords Matched: critical, asap, payment, invoice
```

**Output:**
```
Category: Urgent
Priority: 9
Action: Respond immediately with acknowledgment template. Flag for manual review (financial > $500). Escalate to human handling.
Response Template: Acknowledgment
Escalate: yes — financial amount > $500, client frustration detected, payment system issue
```

---

### Example 2: Business (Invoice Received)
**Input:**
```
From: billing@saasprovider.io
Subject: Invoice #INV-2026-0451 for February
Body: Hi, please find attached your monthly invoice for $49.99. Payment is due within 30 days. Thank you for your continued business.
Keywords Matched: invoice, payment
```

**Output:**
```
Category: Business
Priority: 5
Action: Forward to accounting, log in [[Business_Goals]] for subscription tracking. Review within 1 week.
Response Template: Acknowledgment
Escalate: no
```

---

### Example 3: Personal (Social Invitation)
**Input:**
```
From: ali.khan@gmail.com
Subject: Dinner this Friday?
Body: Hey! A few of us are getting together for dinner this Friday at 7pm. Would love for you to join. Let me know!
Keywords Matched: (none)
```

**Output:**
```
Category: Personal
Priority: 4
Action: Check calendar and respond with availability. Add to personal calendar if attending.
Response Template: (none — informal reply)
Escalate: no
```

---

### Example 4: Spam (Phishing Attempt)
**Input:**
```
From: security-alert@g00gle-verify.xyz
Subject: Your account has been compromised!! Act NOW
Body: Dear Customer, We have detected unusual activity on your account. CLICK HERE to verify your identity immediately or your account will be suspended within 24 hours!!! This is your FINAL WARNING.
Keywords Matched: (none — unknown sender)
```

**Output:**
```
Category: Spam
Priority: 1
Action: Delete immediately. Do not click any links. Mark as spam in email client.
Response Template: (none)
Escalate: no
```

---

## Escalation Rules

| Condition | Escalation Action |
|-----------|-------------------|
| Financial > $500 | Flag for manual review |
| Legal mention | Do not auto-respond, flag |
| Complaint/angry tone | Flag for human handling |
| Unknown high-priority sender | Verify before action |
| Attachment > 10MB | Flag, may need manual download |

## Integration

- Route urgent emails to [[Dashboard]] Active Tasks
- Log financial emails in [[Business_Goals]]
- Follow [[Company_Handbook]] communication guidelines
- Reference [[email_classifier]] for categorization logic
