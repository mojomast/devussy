# Updating Phase Completion in devplan.md

When you complete steps within a phase, update both the phase file and the main devplan dashboard.

Use these anchors in devplan.md:

- Per-phase status (replace N with the phase number):

```
<!-- PHASE_N_STATUS_START -->
phase: N
name: <phase title>
completed: X/Y
<!-- PHASE_N_STATUS_END -->
```

- Overall logs and planning:
```
<!-- PROGRESS_LOG_START -->
... bullet list of completed steps with numbers ...
<!-- PROGRESS_LOG_END -->

<!-- NEXT_TASK_GROUP_START -->
... the next N steps you will do ...
<!-- NEXT_TASK_GROUP_END -->
```

In phaseX.md, summarize your progress between:
```
<!-- PHASE_PROGRESS_START -->
... 2–5 bullets of outcomes, files changed, blockers ...
<!-- PHASE_PROGRESS_END -->
```

This flow ensures the dashboard reflects actual phase completion alongside the per-phase narrative.
