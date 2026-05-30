# Core Link Watch And Future Game Relationship

This document captures how the Wear OS watch experience relates to the future
2D PC/handheld game.

## Product Strategy

The watch is not the small version of the full game. It is the always-with-you
companion layer.

The watch lets the player:

- stay connected to companions
- generate Charge through movement
- maintain and progress companions while away
- receive world news
- read recovered logs
- answer messages
- accept light contracts
- trade and craft small items
- keep the lore warm between main-game sessions

The future 2D game lets the player:

- explore the world
- meet factions physically
- battle and hack
- scavenge directly
- visit towns/zones
- run major missions
- progress hard canon story

## Canon Layers

Use three layers:

- **Hard Canon**: major 2D game story, major faction outcomes, major characters.
- **Soft Canon**: watch contracts, World Pulse, reputation nudges, side contacts.
- **Personal Canon**: companion personality, memories, trust, logs, body evolution.

The watch can influence soft and personal canon. It should not decide major
campaign outcomes unless the future game explicitly supports it.

## Boot Sequence

The watch should always have a boot sequence. It is the Core Link brand ritual.
It does not need to be treated as a one-time global event.

Boot variants:

- **Discovery Boot**: new local/watch-first player.
- **Linked Operator Boot**: game-first/account-linked player.
- **Degraded/Offline Boot**: no network or local-only mode.

Discovery Boot can show:

```text
INITIALIZING CORE LINK...
owner unknown
void cache partial
dormant AI core detected
microfabricator capsule present
```

Linked Operator Boot can show:

```text
INITIALIZING CORE LINK...
operator recognized
companion cache available
relay sync pending
field extension online
```

## Account Posture

Do not require an account for the local-first watch MVP.

Account is required later for:

- purchases
- cloud backup
- cross-device void storage
- future 2D game sync
- restoring progress on a new device
- account-tied Relay contracts

If purchases arrive, they require account. Avoid selling filled Charge directly.

## Sync Philosophy

Do not let future sync complexity distort the watch MVP.

The watch can stand alone. Future sync can be a bonus, not a day-one hard
dependency.

When sync exists, Charge should be transferable between the wrist Core Link and
the 2D game profile. Transferring Charge into the game subtracts it from the
watch reserve, and Charge generated in game can be sent back to the watch. This
preserves the illusion that Core Link is moving stored energy between connected
surfaces instead of duplicating resources.

Formal sync protocol term: **BICOL** / **Bi-directional Core-Link**. The name
also carries a subtle Philippines/Bicol reference while still working as
in-universe technical language.

Overcharge can represent a temporary second energy reserve above the normal
capacitor bar. Normal Charge reads yellow/orange; Overcharge reads blue,
blue-green, or cyan.

If the future 2D game supports importing watch state, the most important data to
carry forward is:

- selected companion/core identity
- Core Matrix/personality
- trust/bond history
- chassis or visual identity
- selected items/materials
- recovered log flags
- reputation snapshots
- contract history summaries

The transfer should feel like importing a relationship, not just importing stats.

## Relay Dock / Core Link Terminal

Full synchronization with the future 2D game can unlock after the player finds,
repairs, or activates a Relay Dock/Core Link Terminal in the 2D game.

Lore reason:

- the watch is a field unit
- the terminal provides stable bandwidth
- the terminal verifies operator identity
- it safely decrypts old ownership locks
- it enables large-item/material transfer
- it reconciles companion history
- it opens full Void Storage bridge access

Watch-first player:

- can play watch independently
- later starts 2D game
- game detects field Core Link history if linked
- full import waits for Relay Dock/Terminal

Game-first player:

- finds/repairs Core Link systems in game
- later opens watch app
- watch performs linked operator boot
- companion/watch mode becomes field extension

## Avoiding Friction

Anything the watch can do should eventually be available in the 2D game after
the player unlocks equivalent knowledge, tools, or network access.

This prevents the watch from becoming a required progression bottleneck.

Examples:

- watch crafting recipes become available in-game later
- watch trade networks map to terminals/vendors later
- watch contracts can appear as leads or side mission history
- watch companions can be imported after sync unlock
