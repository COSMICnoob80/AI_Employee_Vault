# Email Classifier Skill

## Description
Analyzes email content to categorize incoming messages into actionable categories, assigns priority scores, and suggests appropriate actions. Helps triage inbox efficiently by parsing sender, subject, and body.

## Capabilities
- Classify emails into 4 categories: Urgent, Business, Personal, Spam
- Assign priority scores (1-10) based on content analysis
- Suggest specific actions for each email
- Detect time-sensitive keywords and deadlines
- Identify known senders vs unknown contacts
- Flag suspicious patterns (phishing, promotional)

## Input Format
```
Sender: [email address or name]
Subject: [email subject line]
Body: [email body content]
```

## Output Format
```
Category: [Urgent | Business | Personal | Spam]
Priority: [1-10]
Action: [Suggested action]
Reasoning: [Brief explanation]
```

## Rules

### Category: Urgent (Priority 8-10)
1. Contains time-sensitive keywords: "asap", "urgent", "deadline", "critical", "immediately", "emergency"
2. Mentions specific deadlines within 24-48 hours
3. From known important contacts (boss, clients, family)
4. Subject contains "RE:" with urgent context
5. Action required before end of day

### Category: Business (Priority 4-7)
1. From work/professional domain addresses
2. Contains business keywords: "meeting", "project", "invoice", "proposal", "contract", "review"
3. Formal tone and professional signature
4. Requests response but no immediate deadline
5. Related to ongoing work projects or professional matters

### Category: Personal (Priority 3-6)
1. From known personal contacts (friends, family, non-work)
2. Informal tone, casual language
3. Contains personal topics: events, plans, greetings, updates
4. Non-commercial, non-promotional content
5. Social invitations or personal requests

### Category: Spam (Priority 1-2)
1. Unknown sender with generic greeting ("Dear Customer")
2. Promotional language: "sale", "discount", "limited offer", "act now", "click here"
3. Contains "unsubscribe" link indicator
4. Suspicious patterns: ALL CAPS, excessive punctuation, typos
5. Requests sensitive information or contains suspicious links
6. Mass-mailing indicators: no personalization, generic content

## Examples

### Example 1: Urgent
**Input:**
```
Sender: boss@company.com
Subject: URGENT: Client presentation needs revision ASAP
Body: The client meeting is tomorrow at 9 AM. We need to revise slides 5-10 before EOD today. Please confirm you can handle this.
```

**Output:**
```
Category: Urgent
Priority: 9
Action: Respond immediately and begin slide revisions. Block calendar for this task.
Reasoning: Time-sensitive deadline (EOD today), from supervisor, explicit "URGENT" flag, critical business impact.
```

---

### Example 2: Business
**Input:**
```
Sender: vendor@supplierco.com
Subject: Q1 Invoice #4521 Attached
Body: Please find attached the invoice for services rendered in Q1. Payment terms are Net 30. Let us know if you have any questions.
```

**Output:**
```
Category: Business
Priority: 5
Action: Forward to accounting, log in [[Business_Goals]] for subscription tracking. Review within 1 week.
Reasoning: Professional invoice, standard payment terms, no immediate deadline, financial tracking needed.
```

---

### Example 3: Personal
**Input:**
```
Sender: john.friend@gmail.com
Subject: Weekend BBQ at my place
Body: Hey! Having a BBQ this Saturday around 4pm. Bring your family if you want. Let me know if you can make it!
```

**Output:**
```
Category: Personal
Priority: 4
Action: Check calendar and respond with availability. Add to personal calendar if attending.
Reasoning: Known personal contact, informal invitation, social event, no professional relevance.
```

---

### Example 4: Spam
**Input:**
```
Sender: noreply@deals-unlimited-offers.xyz
Subject: YOU WON!!! Claim your $1000 gift card NOW!!!
Body: Congratulations Dear Customer! You have been selected for an exclusive offer. CLICK HERE to claim your prize before it expires!!! Act now - limited time only.
```

**Output:**
```
Category: Spam
Priority: 1
Action: Delete immediately. Do not click any links. Mark as spam in email client.
Reasoning: Unknown sender, suspicious domain, excessive punctuation, generic greeting, classic phishing patterns, no personalization.
```

---

## Integration

- Route **Urgent** items to [[Dashboard]] Active Tasks
- Log **Business/Financial** emails in [[Business_Goals]]
- Follow [[Company_Handbook]] guidelines for response tone
