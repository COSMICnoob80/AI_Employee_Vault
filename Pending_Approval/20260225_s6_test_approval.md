---
type: approval_request
action_type: data_deletion
requested: 2026-02-25T22:45:00
status: pending_approval
priority: high
threshold_exceeded: data_modification
requester: AI_Employee
---

# Approval Request: Delete Old Archive Records

## Action Summary
Delete archived client records older than 2 years from backup storage.

## Details
- **Target**: Archive/client_records_2024/
- **Files**: 47 records
- **Purpose**: Storage cleanup per data retention policy
- **Threshold**: Permanent data deletion requires approval

## Risk Assessment
- **Impact**: High (irreversible data removal)
- **Reversibility**: None (permanent deletion)
- **Cost**: 0 PKR

## Approval Actions
- [ ] **Approve**: Move this file to `/Approved/` folder
- [ ] **Reject**: Delete this file or add rejection reason below
- [ ] **Defer**: Add comment and leave in `/Pending_Approval/`

## Rejection Reason (if applicable)
_None_
