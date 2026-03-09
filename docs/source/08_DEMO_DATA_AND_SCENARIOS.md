# Demo Data and Scenarios

## Machine
- machine_id: `HAAS_VF2_01`
- machine_name: `Haas VF-2`
- machine_type: `CNC_MILL`

## Operators
Use these demo operators:
- OP_001 — Albert
- OP_002 — Ardin
- OP_003 — Demo Operator

Use simple demo PINs during development. Change them later if needed.

## Demo jobs

### Job 1
- job_id: `JOB_201`
- part_name: `Support Plate`
- material: `S355`
- target_quantity: `10`
- drawing_file: `/drawings/support_plate.pdf`
- status: `PENDING`

### Job 2
- job_id: `JOB_202`
- part_name: `Mounting Bracket`
- material: `Aluminum`
- target_quantity: `8`
- drawing_file: `/drawings/mounting_bracket.pdf`
- status: `PENDING`

### Job 3
- job_id: `JOB_203`
- part_name: `Machined Shaft`
- material: `C45`
- target_quantity: `25`
- drawing_file: `/drawings/machined_shaft.pdf`
- status: `PENDING`

## Scenario 1 — Normal Production
Purpose:
Show clean digital workflow.

Flow:
1. operator login
2. select `JOB_201`
3. open drawing
4. start setup
5. confirm setup
6. start cycle
7. let simulator generate parts
8. finish job
9. show COMPLETED then IDLE

What this proves:
- digital job handling
- live machine states
- live produced count
- event timeline
- dashboard visibility

## Scenario 2 — Interrupted Production
Purpose:
Show interruptions, scrap, and AI value.

Flow:
1. operator login
2. select `JOB_202`
3. open drawing
4. start setup
5. confirm setup
6. start cycle
7. manually trigger alarm with `TOOL_WEAR`
8. add note: `Insert started vibrating during cut`
9. show AI reason suggestion
10. clear alarm
11. resume cycle
12. report scrap:
    - quantity: 1
    - reason: DIMENSION_OUT
    - note: Diameter out of tolerance
13. run AI summary or downtime analysis

What this proves:
- alarm handling
- operator notes
- AI assistance
- scrap reporting
- downtime interpretation

## Suggested AI prompt outputs during demo

### Reason suggestion example
Input note:
`Insert started vibrating during cut`

Suggested reason code:
`TOOL_WEAR`

### Downtime analysis example
`Two interruptions occurred during production. Both were associated with tooling conditions. Average pause duration was approximately 3 minutes. Consider reviewing insert wear intervals.`

### Summary example
`During the current run the machine produced 8 parts. One alarm occurred due to tooling wear. One scrap part was reported due to dimension being out of tolerance.`
