# Core Link Watch UI And Systems Draft

This document captures the rough watch experience direction. Use it when
designing Core Link Wear OS screens, tasks, QA criteria, or implementation
briefs.

## Product Role

The watch is the always-with-you companion and world-connection layer. It is not
the full RPG squeezed onto a tiny screen.

The watch should keep the player connected to:

- their AI companion
- movement-generated Charge
- recovered logs
- Relay messages
- World Pulse updates
- short contracts
- light trades
- repair, scan, and roam actions

Future PC/handheld/2D game surfaces should handle major exploration, battles,
towns, faction story, and hard canon progression.

## Primary Home Screen

The main screen is **Core Link Home**: a single glanceable OS command surface.
The companion is the center of the screen. Metrics support the companion; they
are not the product.

Wireframe:

```text
+-------------------------+
| CORE LINK        RELAY 2|
| CHG 72  SCR 18  COND 84|
|                         |
|      [ pixel bot ]      |
|    idle / scan / roam   |
|                         |
| "Mote found a weak ping"|
|                         |
| [SCAN] [REPAIR]         |
| [ROAM] [RELAY]          |
+-------------------------+
```

The home screen should answer quickly:

- Is my companion okay?
- Do I have Charge?
- Is there anything new?
- What can I do right now?
- Is the world calling me back?

## Navigation

Keep navigation shallow and watch-native.

- Tap companion: companion detail, mood, memory/core status.
- Tap `RELAY`: messages, contracts, world pulse, owner-locked packets.
- Tap `SCAN`: diagnostic scan or log recovery chance.
- Tap `REPAIR`: repair if resources allow.
- Tap `ROAM`: send or recover bot.
- Use vertical scroll only for detail surfaces.

Avoid a crowded bottom tab bar. Use contextual panels and clear command buttons.

## Core Surfaces

### Boot And Recovery

The watch should always have a Core Link boot sequence. The boot is a brand
ritual and device fantasy, not necessarily a one-time global canon event.

Variants:

- **Discovery Boot**: owner unknown, damaged cache, AI core recovery.
- **Linked Operator Boot**: operator recognized, companion sync, Relay enabled.
- **Degraded/Offline Boot**: local field mode, limited Relay, stored companion available.

### Core Link Home

Daily check-in surface with animated bot, compact HUD, alert line, and four
primary commands.

### Relay

World-contact surface for messages, contracts, owner packets, trade offers, and
World Pulse updates.

Example:

```text
RELAY
WORLD PULSE
CONTRACT
OWNER LOCK
BACKCHANNEL?
```

### Contract Detail

One decision at a time. Keep contracts readable in seconds.

```text
RELAY CONTRACT
need: 2 Servo Bundles
offer: Energy Tank Mk I
risk: Foundry trace
[ACCEPT] [PASS]
```

### Log Recovery

Recovered memories, owner fragments, field reports, or system records. Start
clinical and broken. Become more personal over time.

### Companion Detail

Mood, condition, trust/memory/core status, matrix traits, and body/chassis
identity. Keep this compact and avoid spreadsheet presentation.

## Visual Direction

Style: salvage cyberpunk pixel OS.

- Background: near-black blue/green terminal surface.
- Primary glow: cyan/teal.
- Warning: amber.
- Danger: red/magenta.
- Recovery/repair: soft green.
- Rare/void: violet.
- Type feel: compact monospaced/system diagnostic.
- Art language: pixel bot, scan lines, subtle glitch, waveform lights, relay blips.

The AI core faceplate should remain visible in the bot chassis. It pulses with
voice and mood:

- idle: soft cyan pulse
- speaking: waveform brightness
- low power: dim amber flicker
- angry/danger: sharp red scan bars
- curious/scan: violet rings
- damaged: broken light segments
- trusting/stable: slow clean glow

## Interaction Feel

The watch should feel quietly alive.

- Bot idles even when nothing is happening.
- Relay badge pulses when new messages arrive.
- Low Charge dims or flickers the companion.
- Repair triggers a microfabricator swarm animation.
- Roam shows the bot leaving, signal trail, or remote status.
- Scan sweeps over the core/body.
- Log recovery appears as reconstructed lines, not generic popups.

Use haptics for command confirmation, warning states, and recovery success when
available. Keep sounds optional and lightweight.

## Watch Time Budget

Most sessions should fit into short check-ins:

- 5-20 seconds for normal check-in.
- One decision per screen.
- No map traversal.
- No long dialogue trees.
- No battle system in the watch MVP.
- No deep inventory management on the watch.

## Systems Shown On Watch

Initial watch systems:

- Charge
- Scrap
- Condition
- companion mood/state
- Scan
- Repair
- Roam
- Relay
- World Pulse
- recovered logs

Later watch systems:

- contracts
- trade network offers
- crafting from known recipes
- Core Cache status
- microfabricator capsule status
- material loadout
- companion import/export status
- account/operator registry

## Guardrails

- Do not make the primary screen a card dashboard.
- Do not bury the companion behind metrics.
- Do not make the watch a full RPG menu system.
- Do not require account for the local-first MVP.
- Do not sell filled Charge as a shortcut.
- Do not make watch-exclusive crafting levels.
- Do not let watch actions rewrite major canon story.
- Do preserve soft consequences through news, reputation, contacts, resources,
  companion reactions, and optional future sync.
