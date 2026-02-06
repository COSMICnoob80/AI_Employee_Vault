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
