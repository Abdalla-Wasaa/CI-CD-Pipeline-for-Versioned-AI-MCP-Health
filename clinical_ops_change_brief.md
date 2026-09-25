# Change brief for clinical_ops

## What changed
This classroom demonstration now checks a proposed software release before allowing
it to move forward. It records which instructions and clinic-support service belong
together, and can restore the previous demonstration release. No real patients or
live clinic systems are connected.

## What was tested
The stable instructions were checked against ten made-up examples. A deliberately
weaker proposal is rejected. Checks also verify that the clinic-support service
responds and provides the expected information. A rehearsal restores the previous
release record. These checks demonstrate release controls, not clinical accuracy.
Detailed results are in `docs/verification.md`.

## Rollback
Ask engineering to restore the last approved release as a complete package, verify
that the service works, and report the restored version. Clinical operations confirms
that it is acceptable to resume use. In this demo, restoration changes a local record;
it does not change a live service.

## Approvers
Clinical operations lead: pending named reviewer and decision.
Engineering reviewer: pending human review.
Accountable release owner: pending final decision.

## Go / No-Go recommendation
Go for a supervised classroom demonstration if the recorded checks pass.
No-Go for patient-facing use: human approval, broader clinical evaluation, access
controls and a real deployment rehearsal are still required. A failed release check
means stop and review; do not bypass it to meet a deadline.
