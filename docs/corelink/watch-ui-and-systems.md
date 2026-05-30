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

Current simplified layout direction:

```text
        capacitor charge arc
    [■■■■■■□□□□□□]  upper half

       +2 Charge - 200 steps | 09:42

   empty slot  [ animated active bot ]  filled slot
       ○               ◉                 ●

          "translated bot line..."

      [condition] [sync]  (menu)  [mood] [signal]
```

The home screen should answer quickly:

- Is my companion okay?
- Do I have Charge?
- Is there anything new?
- What can I do right now?
- Is the world calling me back?

Home screen decisions:

- Show Core Link capacitor Charge as a segmented half-moon arc around the top of
  the watch. Each segment represents a portion of current/max Charge.
- The number of Charge segments can grow as max capacitor capacity increases.
- Directly below the capacitor arc, show the latest Charge activity summary, for
  example `+2 Charge - 200 steps | 09:42`.
- Put the currently selected bot in the center as animated pixel art.
- Represent up to two other active bot slots as small side circles to the left
  and right of the active bot.
- Swipe left/right to switch active bot only when the destination slot is filled.
- Empty bot slots remain visible but inactive so the player understands the
  future three-bot squad shape.
- Show only compact bot status on the home screen: condition, mood, and one or
  two context-critical stats.
- Tapping the capacitor arc opens a dedicated capacitor screen.
- Tapping compact bot stats opens a dedicated bot status screen.
- Tapping the bot is an emotional interaction, not the command menu.
- Bot tap should play a small heart/affection animation like petting the
  companion and may give a small mood boost.
- Reserve a small text space on the home screen for the active bot's latest
  translated line, short thought, or status phrase when it has something to say.
- Show bot mood with a larger bubble indicator pointing to the bot when the
  pixel body/core face is too small to read clearly.
- If the bot has unread speech/history, show a blinking message icon.
- Tapping the message icon opens the companion speech log.
- Put one larger circular command/menu button in the lower center of the watch.
- The menu button opens the top-level command menu.
- Compact status chips can sit around the lower half of the watch: condition,
  sync or stability, mood, signal/Relay, or another context-critical stat.

Top-level command menu after tapping the bot:

- **Energy**: battle later, roam, scan, Charge-related actions.
- **Tinker**: repair, craft, upgrade.
- **Relay Console**: messages, contracts, World Pulse, owner packets.
- **Manage**: bot list, inventory, storage, settings, future account/sync.

The previous idea of always showing four command buttons on the bottom arc is
not the current direction. Prefer a calmer home screen with actions revealed
after tapping the active bot unless testing proves the extra tap feels bad.

Open question for later: decide whether bot-specific inventory follows the
active bot directly or whether all bot/core inventory lives under a global
management screen.

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

The discovery boot should maintain the illusion that the user has picked up
lost technology booting for the first time in a long time. It is acceptable if
the sequence briefly feels alarming, like the watch may be compromised or
hijacked by an unknown OS. That attention-grab is part of the fantasy.

The recovery flow should avoid meta explanations. Do not tell the user that
their answers are configuring a personality system. The experience should feel
like Core Link OS is reaching real recovery problems and needs operator input.
Behind the scenes, each answer tunes AI companion personality, Core Matrix
values, and starter tendencies.

Discovery boot principles:

- Use OS diagnostics, warnings, corrupted logs, access prompts, and recovery
  questions instead of narrator prose.
- Ask technical-feeling questions that ordinary players can still understand.
- Present one recovery problem at a time.
- Use about 4 required recovery roadblocks before the starter core becomes
  usable. Add optional later recovery prompts through logs, repairs, Relay, and
  companion events rather than making the first session too long.
- Each step should feel necessary to recover the AI core, not like a quiz.
- Do not front-load lore or explain the personality matrix.
- Let story emerge naturally from recovered logs, Relay messages, contracts,
  device state, and companion reactions.
- Avoid any "time out, here is the lore" presentation.

Recovery sequence structure:

1. Core Link discovers a recoverable AI core.
2. Core Link asks whether to begin the recovery process.
3. If accepted, Core Link shows live diagnostic logs: processing, analyzing,
   scanning lattice, checking cache, routing power, testing language/protocol,
   and inspecting chassis intent.
4. The process hits a roadblock.
5. Core Link describes the problem in practical OS language and asks the user to
   choose a direction.
6. The user's choice resolves or redirects the roadblock, then diagnostics
   continue.
7. Repeat for about 4 recovery roadblocks before the AI core is usable.

Each roadblock should feel like:

```text
ANALYSIS PAUSED
conflict detected: [specific technical system problem]
operator input required:

[A] technical recovery option
[B] technical recovery option
[C] technical recovery option
```

Each answer should secretly tune the AI companion personality, stats, language
behavior, chassis tendency, or early mood, but the UI must not make that obvious.
Do not ask direct personality questions such as "are you cautious or bold?"
Instead, ask technical recovery questions whose options imply user preferences.

Example shape:

```text
MEMORY LATTICE RECOVERY
nexus relay instability detected
primary path cannot sustain clean read
operator decision required:

[A] bypass relay through hyperline shunt
[B] throttle core draw and rebuild route
[C] sample unstable path before reroute
```

The user sees a believable Core Link OS recovery decision. Behind the scenes,
the answer can imply preferences such as speed, safety, curiosity, risk
tolerance, efficiency, repair-first thinking, or trust in unstable signals.

Variants:

- **Discovery Boot**: owner unknown, damaged cache, AI core recovery.
- **Linked Operator Boot**: operator recognized, companion sync, Relay enabled.
- **Degraded/Offline Boot**: local field mode, limited Relay, stored companion available.

Example recovery step shape:

```text
CORE LINK RECOVERY
signal fork detected
route limited power to:

[A] stabilize AI core
[B] restore Relay handshake
[C] scan void cache
```

The user sees a practical recovery decision. The system can secretly infer
values such as caution, curiosity, discipline, loyalty, independence, or
efficiency from the choice.

Example tone:

```text
INITIALIZING CORE LINK...
boot age: unknown
operator: not recognized
watch bridge: unauthorized
void cache: sealed
ai core: dormant

RECOVERY INPUT REQUIRED
```

This should feel like a real OS in a real universe, not onboarding copy.

### Core Link Home

Daily check-in surface with animated bot, capacitor arc, latest Charge activity
summary, compact bot state, side-slot indicators, and one larger lower-center
menu button. Touching the bot should feel like petting/acknowledging the
companion; commands live behind the menu button.

### Companion Speech Log

All bots in this universe can communicate. Some speak the operator's language.
Some speak another human language, machine dialect, faction protocol, corrupted
matrix speech, or partially damaged language. The bot status/spec screen should
list this as the bot's **Language**.

Core Link should auto-translate bot speech for the operator when possible. The
translation should feel real-time: the interface should preserve the illusion
that Core Link is translating as the operator reads, not merely showing static
pretranslated text.

Home behavior:

- Show a short latest translated line on the main screen when relevant.
- Show a blinking message icon when the active bot has something unread to say.
- Keep the line brief enough that it does not compete with the bot visual.

Speech log behavior:

- Tapping the message icon opens a scrollable text screen.
- Show current and past bot lines with timestamps.
- Preserve the feeling of a communication log, not a chat app.
- The bot's original language/protocol can be hinted at but should not block
  comprehension.

First-time translation effect:

- If the bot speaks another language or protocol, show the original/garbled
  glyphs briefly.
- Animate letters changing in real time into the user's current language.
- Treat this as Core Link translation coming online, not a narrator explanation.

Routine translation effect:

- Show a lighter raw-to-translated flicker or word morph for normal messages.
- Keep routine translation fast enough that it does not annoy repeat users.
- Use the stronger reveal for first contact, rare language discovery, corrupted
  speech, important memory fragments, or dramatic story lines.

Example:

```text
09:42  [raw]  ka...ren seth // no-home signal
09:42  [link] I remember a signal. Not a place.
09:44  [link] Your hand pattern is familiar now.
```

### Mood Emoji / Glyph Bubble

AI cores can learn human social habits, including the use of emojis or simple
glyphs to signal mood. In-universe, many bots display these symbols on their
core faceplate because humans use similar symbols to communicate emotion.

On the watch, the pixel bot and exposed core face may be too small to read
clearly. Use a larger speech-bubble-like mood indicator pointing to the active
bot when needed.

Rules:

- Treat emoji/glyph mood as something the AI chooses to display, not a UI sticker
  pasted on by the app.
- The bubble should appear to come from the bot/core.
- Use it for mood, affection, surprise, confusion, distress, curiosity, or
  attention.
- Keep it lightweight and occasional so it feels expressive, not spammy.
- Use Core Link-styled glyphs where standard emoji feel too modern or off-tone.

Examples:

- heart/affection after petting
- question mark or curious glyph after a scan
- warning glyph when low power
- sleepy glyph when idle/low energy
- spark/exclamation when a Relay ping interests the bot

Communication variants:

- Some AI cores may be nonverbal and communicate entirely through emojis,
  symbols, glyphs, motion, sounds, or faceplate patterns.
- Some bots may mix translated speech with emoji/glyph shorthand.
- Some damaged, childlike, experimental, or deliberately minimalist cores may
  prefer symbol-only communication even when translation is technically possible.

Rogue/unstable mood variant:

- A rare unstable rogue AI can treat mood like a slot machine.
- Its faceplate cycles rapidly through emojis/glyphs and randomly lands on one.
- The selected symbol becomes its actual mood/state, not just a visual gag.
- This can drive unpredictable behavior, battle stance, dialogue tone, or
  command response until the mood shifts again.

Example:

```text
MOOD ROULETTE
cycle: ♥ ? ! ⚠ ...
selected: ⚠
state: volatile / defensive
```

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

### Capacitor Detail

Opened by tapping the capacitor arc. Show a vertical technical readout with
segmented bar graphics:

- current Charge
- max Charge
- capacitor health
- capacitor version
- charge generation status
- recent activity conversion

Use segmented bars made of filled/unfilled rectangles rather than smooth
progress bars.

### Bot Status Detail

Opened by tapping compact bot stats. Show deeper bot state with text labels on
the left and segmented bars on the right. For example, Speed `3/10` is three
filled rectangles and seven unfilled rectangles.

Use this surface for deeper stats that cannot fit on the home screen. Keep the
home screen limited to the selected bot's most urgent state.

Include **Language** as a visible bot spec. This identifies the bot's native
speech mode before Core Link translation.

The player cannot select or customize a bot's native language. A bot's Language
is programmed at manufacture time or inherited from its core/personality matrix
origin. It is a discovered/spec trait, not a settings option.

The player can select their own operator/app language. Core Link translates bot
speech from the bot's native Language into the user's selected language whenever
translation is available.

Translation rendering should still feel live. Even when the final message is
known, show a brief transformation from native bot language/protocol into the
operator's selected language so the magic of Core Link translation remains
visible.

Language examples:

- English
- Tagalog
- Japanese
- Machine Dialect
- Faction Protocol
- Corrupted Matrix Speech
- Unknown / Untranslated

The player should see the bot's native language/spec, while Core Link can still
translate speech into the user's current language.

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

Bots can also display small emojis/glyphs directly on the core faceplate as
mood shorthand. On small watch views, mirror or enlarge that expression in a
nearby bubble so the operator can actually read it.

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
