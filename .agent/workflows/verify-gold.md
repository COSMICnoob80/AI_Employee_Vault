---
description: Verify the Gold tier system implementation status against SPEC.md.
---

# verify-gold

* Read `SPEC.md` Gold tier section
* For each checked Gold item (G1-G4), verify the corresponding script exists and passes `ast.parse`
* For each unchecked Gold item (G5-G7), report what's missing
* Check `VERIFICATION_REPORT.md` matches `SPEC.md` state
* Report discrepancies

## Agent Manager for G7 Browser Testing
When I use you to build the social media posting pipeline, you have to use Antigravity's Browser Subagent:

"Test the Facebook posting flow: navigate to facebook.com, verify login state, attempt to create a post with test content, screenshot the result. Do NOT submit the post."

This generates screenshots + browser recordings as artifacts — verifiable evidence for judges.
