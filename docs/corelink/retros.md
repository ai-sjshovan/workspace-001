# Core Link Retrospectives

Record lessons from completed runs, QA failures, and product pivots.

## Dashboard Drift Correction

- Earlier Core Link tasks preserved native Wear OS mechanics but collapsed the product into cards, counters, and simple dashboard panels.
- Root cause: workers received acceptance criteria but not enough product-experience context per task.
- Correction: Core Link now has a worker brief injected into Symphony prompts, and visual/game QA must reject static card/counter implementations when a game scene is expected.
