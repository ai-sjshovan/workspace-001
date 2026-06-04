# Core Link Worker Brief

This brief is required context for Core Link implementation tasks. Use it to understand the product experience behind the task checklist.

For deeper universe, progression, mechanics, and lore context, read
`knowledge/projects/corelink/lore-product-brief.md`.

For watch-specific UI, Relay, contracts, boot variants, and interaction
guardrails, read `knowledge/projects/corelink/watch-ui-and-systems.md`.

For broader design context, also consult these focused briefs when relevant:

- `knowledge/projects/corelink/world-and-factions.md`
- `knowledge/projects/corelink/core-tech-and-bot-assembly.md`
- `knowledge/projects/corelink/relay-contracts-and-world-pulse.md`
- `knowledge/projects/corelink/watch-game-relationship.md`

## Product Intent

Core Link is a native Wear OS pixel game prototype. It should feel like the player recovered a high-tech wrist device that boots into Core Link OS and discovers a damaged AI core plus a full nanobot container. It is not a dashboard, CRUD app, tracker, or metrics panel.

Use the name `Core Link` in player-facing text. Do not call it a rig.

## First-Time Experience

The first launch should be an OS-guided boot/recovery sequence, not narrator prose.

- Show `Initializing Core Link...`, wait briefly, then reveal scrolling diagnostic log lines.
- Report device state through Core Link OS style messages: owner unknown, memory lattice tampering detected, AI core unstable, nanobot container full.
- Show connected resources such as `1x AI Core` and `1x Nanobot Container (Full)`.
- Ask whether to recover items and then analyze the AI core.
- Present one technical recovery/calibration question at a time. Each answer should reveal something about the player and shape the starter AI core personality/stats.

## Main Game Scene

The primary app surface is a single watch-sized game scene.

- Put an animated pixel Nanobot Core companion in the center.
- Keep Charge, Scrap, and Condition as compact HUD data, not the main content.
- Put only the primary commands at the bottom: Charge, Repair, Roam, Scan.
- Use command icons plus short labels.
- Preserve existing mechanics: Charge, Scrap, Condition, Repair, Roam, Low Power, and local persistence.

## Pixel Art And Feedback

The bot should be pixel-styled and animated with multiple visual states:

- idle pulse
- scan/curious
- low-power/damaged flicker
- repair/nanobot swarm
- roam/dispatch
- happy/recovered

Add native Compose animation where possible. Add Wear OS haptics for command taps, warnings, and recovery success when available. Add lightweight sound cues only if feasible without heavy assets or external services.

## Hard Anti-Patterns

- Do not ship a card-heavy dashboard as the primary experience.
- Do not rely on static counters and simple calculations as the product.
- Do not use WebView, HTML, CSS, JavaScript, or a browser substitute.
- Do not bury the bot behind telemetry.
- Do not add long narrator copy. Let Core Link OS guide the player through diagnostics and prompts.
