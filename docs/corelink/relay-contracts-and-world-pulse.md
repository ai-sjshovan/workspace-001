# Core Link Relay, Contracts, And World Pulse

This document captures how the watch stays connected to the world without
becoming the full RPG.

## Product Role

Relay is the watch's world-contact layer. It gives the player messages,
contracts, trades, rumors, faction pressure, and news while away from PC or
handheld.

Relay should feel like an in-universe network, not a generic inbox.

Story channels:

- **Recovered Logs**: the past.
- **Relay Messages**: active world contact.
- **World Pulse**: ambient world updates.
- **Contracts**: short decisions that affect resources, reputation, or soft world state.

## Message Types

- **Owner-Locked Messages**: meant for the previous Core Link owner.
- **Dead Drops**: delayed, encrypted, or location/context-triggered packets.
- **Faction Broadcasts**: propaganda, warnings, threats, recruitment.
- **Encrypted Replies**: messages the player can answer.
- **Bot Whispers**: messages sent directly to the AI core.
- **Corporate Notices**: reclaim, warranty, audit, storage, or security pings.
- **Black-Market Pings**: risky offers from Null Cartel-style sources.
- **Ghost Packets**: damaged fragments from old networks.
- **World Pulse**: short news updates about the world.

Possible surface names:

- Relay
- Core Relay
- Operator Relay
- Ghostline
- Dead Drop
- Packetstream

Current default: use **Relay** for the generic system.

## World Pulse

World Pulse displays short news updates that make the world feel alive.

Examples:

```text
WORLD PULSE
Foundry convoy delayed near Sector 8.
Salvage prices spike after capacitor shortage.
Unlicensed repair shops warned of inspection sweep.
Unknown relay claims 14 cores freed from cold storage.
Circuit League bans unstable reconfiguration chassis class.
```

Player choices can influence World Pulse in subtle ways without breaking the
future 2D game's main canon.

Examples:

- Helping Backchannel reroute firmware can lead to protest/news updates.
- Helping Salvage Houses can improve local repair trust.
- Selling illegal parts can increase Null Cartel chatter.
- Protecting damaged cores can raise Free Core interest.
- Ignoring low-power warnings can make companion logs more fragmented.

## Soft Consequences

The watch can change what the world is talking about and how some optional
contacts react, but it should not rewrite core story.

Allowed watch consequences:

- local news changes
- faction reputation shifts
- optional side contacts
- soft district conditions
- resource flows
- contract availability
- companion reactions
- recovered log variants

Avoid watch consequences that:

- kill major NPCs
- skip main campaign beats
- destroy major locations
- permanently decide faction endings
- make future 2D story impossible to reconcile

## Contracts

Contracts are short decision-based missions suitable for watch check-ins.

Possible contract actions:

- deliver firmware patches remotely
- route power to a locked device
- unlock a disabled repair tool
- scan a junk field for a missing component
- send a bot to recover a part
- repair someone's helper bot
- reroute a corporate shipment
- decrypt a dead drop
- trade Scrap/components for rare items
- stabilize a damaged AI core
- hide a fugitive core from a reclaim scan
- complete a faction request anonymously

Example:

```text
RELAY CONTRACT
sender: backchannel.node/unknown
request: reroute delivery manifest
need: 2 Charge, 1 Signal Key
reward: +Backchannel rep, rare move module
risk: Foundry trace
```

Contracts should fit one-screen decisions:

- Accept
- Pass
- Reply
- Trade
- Dispatch
- Scan
- Recover

## Trades And Markets

Watch trade networks give early access to remote offers before the player
physically reaches equivalent systems in the future 2D game.

Trade examples:

```text
SALVAGE HOUSE OFFER
wanted: 3 Servo Bundles
offering: Energy Tank Mk I
bonus: +local trust
```

Rewards can include:

- Scrap
- specific components
- empty or filled Energy Tanks earned through play
- move modules
- personality matrices
- firmware patches
- signal keys
- cache keys
- chassis parts
- repair kits
- microfabricator capsules

Avoid selling filled Charge directly. Charge should remain tied to movement,
activity, or development simulation.

