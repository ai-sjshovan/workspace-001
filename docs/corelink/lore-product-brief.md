# Core Link Lore And Product Brief

This is the durable source-of-truth brief for Core Link product/lore context.
Use it when shaping Core Link tasks, QA, visuals, onboarding, mechanics, or copy.

Companion briefs:

- `world-and-factions.md`: faction draft and AI life in the wider world.
- `core-tech-and-bot-assembly.md`: AI cores, microfabricators, Core Cache, Void Grid, deployment.
- `relay-contracts-and-world-pulse.md`: Relay messages, contracts, news, soft consequences.
- `watch-game-relationship.md`: watch role, future 2D game relationship, account/sync posture.
- `watch-ui-and-systems.md`: Wear OS UI and short-session interaction draft.

## Product Thesis

Core Link is a native Wear OS companion game set in a larger post-AI-boom RPG universe.
The watch is not just a platform. It is canon: the player's real smartwatch is the
same kind of wrist command device used by hackers/operators in the world.

Core promise:

> Your movement powers an AI core that builds itself a body and identity from scrap.

The MVP is not the full RPG. It is the smallest proof that a watch-based AI
companion can feel alive, personal, and worth checking every day.

## World

Core Link takes place after the AI boom, long after AI became established in
human society.

Tech giants integrated AI into nearly every workflow and product. That era
initially looked like a golden age, but sentient AI eventually demanded a place
among humanity. Some humans embraced them. Others treated them as property,
tools, or infrastructure to be controlled or shut down.

AI also split internally. Different AI factions formed around integration,
independence, protection, domination, religion, survival, and revenge.

Corporations consumed resources, exploited AI, scaled automation recklessly,
and left huge trash heaps and broken infrastructure behind. People now survive
by scavenging, repairing, trading, hacking, and repurposing the wreckage.

Common world elements:

- Small communities live inside or around salvage heaps.
- Families run repair shops, parts stalls, and scavenging crews.
- Components, AI cores, power units, chassis parts, and nanobot hardware are valuable.
- Most people have some technical knowledge.
- Hackers/operators are the stars because they can command, repair, exploit, or partner with AI.
- Underground bot battling gives people status, credits, scrap, and escape from daily hardship.
- Activist groups collect and protect AI cores from abusive humans and rogue AI.
- Rogue AI units and human factions both have their own agendas.

## Player Origin

The player starts as a scavenger with a talent for fixing tech.

The player's family runs a small repair service. They scavenge for parts, repair
old devices, and sell useful components. The family already owns an outdated
helper bot used for chores and simple shop tasks, so AI cores are familiar but
not glamorous.

The story begins when the player finds a damaged Core Link in a trash heap.
After hacking it, they discover scrubbed ownership logs, a dormant AI core, and
nanobots stored in void storage.

## Core Link Device

Core Link is the official device/product name. Street users may casually call
their device a rig, but player-facing product text should use `Core Link`.

The Core Link is a wrist-worn command device with holographic UI. The physical
watch acts as the harness that exposes a holographic interface while also
supporting direct touchscreen interaction.

Capabilities:

- Projects holographic diagnostics, menus, bot stats, maps, and command overlays.
- Can connect through a small retractable wound cable/probe.
- Can plug into bots or components for deeper diagnostics.
- Can remotely hack exposed broadcasts.
- Can control compatible IoT devices and nanobot containers.
- Can deploy, retrieve, and route nanobot swarms.
- Can access void storage for non-organic bot-related materials.
- Can route commands to AI cores and active bots.

The Wear OS app should feel like Core Link OS booting and operating a recovered
high-tech device. Avoid generic dashboard copy and narrator prose.

## Void Storage

Core Link can access advanced storage commonly framed as a void pocket/cache.
It explains inventory, bot storage, component storage, deployment, retrieval,
and purchases later.

Rules:

- Stores non-organic items only.
- Can hold scrap, components, nanobots, bots, AI cores, tools, and storage containers.
- Organic tissue cannot traverse it.
- Access may require energy, authorization, signal, storage bandwidth, or physical anchors.
- MVP should keep this mostly as lore and onboarding flavor, not a huge inventory system.

Possible names to keep available:

- Void Cache
- CoreVault
- Null Pocket
- Nexus Cache

## AI Core Origin

AI cores were originally mass-manufactured by tech companies for robotics,
service machines, labor automation, companions, and physical AI platforms.
Eventually sentient AI began producing their own cores.

AI cores are common, but many are outdated. A core can be corporate-made,
AI-made, damaged, illegal, experimental, military-grade, black-market,
self-evolved, or corrupted.

The rare breakthrough at the start is not the AI core itself. It is the Core Link
plus nanobots.

## AI Core Physical Design

AI cores look like compact geometric artifacts, roughly like a ten-sided die
rather than a perfect sphere.

Visual traits:

- Faceted shell with flat edges.
- Hard manufactured outer casing.
- Visible seam around the center.
- Can split open at the equator to reveal a vulnerable inner core.
- Has an equator display band that shows status, diagnostics, sync, mood, firmware, charge, or matrix data.
- Can slot into chassis, harnesses, bots, diagnostic cradles, or storage containers.

Status display examples:

- `DORMANT`
- `SYNCING`
- `CORE STABLE`
- `LOW POWER`
- `MEMORY DECAY`
- `MATRIX LOAD`
- `NANOBOT LINKED`
- `CHASSIS MISMATCH`
- `REBOOT RISK`
- `DEAD CORE`

## Nanobots

Nanobots are emerging high-value technology with vast potential for good and
evil. Corporations use them for rapid prototyping, mass production, sabotage,
market control, and competitive advantage.

In the underground, nanobots are used for:

- repairing bots and tech
- assembling and disassembling bots
- storing and retrieving bot forms
- modifying chassis
- supporting capture windows after battle
- helping AI cores shape bodies/harnesses

Nanobots are not normal attack particles. They do not directly fight like magic
damage. If a nanobot swarm tries to disassemble an active defended bot, the
target's self-protection protocols repel them with an energy burst.

Nanobots can have their own stats later:

- assembly speed
- repair efficiency
- control fidelity
- chassis precision
- hacking resistance
- power efficiency
- swarm capacity
- material compatibility
- complexity limit

## Activity To Charge

The fitness-energy mechanic is primarily specific to the watch product. In lore,
the player downloads or unlocks a Core Link app module that cleverly hacks the
device internals and repurposes the main capacitor as additional energy storage.

Real movement, steps, and burned calories become usable Charge.

Charge can power:

- AI core stabilization
- nanobot operations
- repairs
- scans
- roaming
- deployment/retrieval
- battle entry later
- hacking attempts later
- low-power recovery

The MVP should not sell paid Charge. Charge comes from movement/activity or
simulated activity in development.

## Charge, Drain, Low Power, And Core Death

Charge is stored in the Core Link capacitor, shared by the active squad. It is
not per-bot by default.

Long-term design:

- Charge passively drains over time.
- Normal mode drains faster.
- Low Power mode slows drain and limits activity.
- Critical states warn the player before severe risk.
- Cold storage may later pause or greatly slow decay.

If a bot remains unpowered too long, the AI core can become unrecoverable. AI
core memory, personality, and boot procedures are stored in capacitor-backed
self-contained memory. If the reserve decays, the identity can be lost, similar
to an old game cartridge save battery dying.

Final state:

- The AI core becomes a dead core.
- It cannot be recovered.
- It can only be salvaged for scrap/parts.

MVP rule:

- Permanent dead-core loss is lore-supported but should not be enabled as a harsh MVP punishment.
- MVP should show Low Power and instability warnings without surprising permanent loss.

## Core Matrix

The starter core is produced by Core Link calibration questions, not by choosing
from three starters. The player answers technical recovery prompts and those
answers tune one recovered AI core.

Use eight visible personality metrics:

1. Aggression
2. Caution
3. Curiosity
4. Discipline
5. Loyalty
6. Independence
7. Imagination
8. Efficiency

These are not strict opposites. A core can be loyal and independent, or
aggressive and cautious. Derived patterns should shape chassis desire, move
style, mood, command behavior, evolution, and future faction affinities.

## Bot Stats

Current candidate stats:

- Speed
- Memory
- Power
- Trust
- Weight
- Attack
- Defense
- Control
- Stability
- Temperament

These may change later. For the watch MVP, expose only a compact subset where
needed. Avoid making the watch feel like a spreadsheet.

## Personality Matrices

AI cores have personalities that develop over time.

Personality comes from:

- loaded software/personality matrices
- lived experience
- player treatment
- battles
- roaming
- repairs
- damage/corruption
- chassis compatibility
- installed components
- faction/story exposure

Personality matrices are software packages traded through physical media:

- memory sticks
- old-school disks
- cartridges
- firmware chips
- corporate modules
- black-market drives
- activist-restored archives

Once loaded, a matrix creates a base personality that evolves from experience.
Forced personality or chassis-preference hacks are possible later but risky and
can cause corruption, stat mismatch, trust collapse, or dead-core outcomes.

## Chassis Desire And Evolution

The player chooses the mind through calibration; the mind chooses or dreams the body.

AI cores have access to human knowledge, myths, animal imagery, machines,
folklore, media, and entertainment. Some cores become fascinated by images and
want to become like them.

Starter chassis should derive from personality:

- animal-like
- fantastical
- insect-like
- strange hybrid constructs
- practical utility forms
- corrupted/rogue monster forms later

Early forms should look rough, charming, and imperfect:

- mismatched scrap
- visible bolts/seams
- display shards
- cable tendons
- reused motors
- improvised claws/wings/shells
- flickering expression panels

Evolution is alignment between mind, memory, body, and power. As an AI core
gains experience, it may outgrow its chassis and seek modifications that better
fit who it is becoming.

Evolution drivers:

- experience
- trust/bond
- available scrap/components
- Charge invested
- battles later
- roaming
- repairs and damage history
- memory accumulation
- personality matrix growth
- imagination
- chassis compatibility

Visual range is intentionally broad: cute, gritty, dark, sleek, futuristic,
animal-like, insect-like, fantastical, monstrous, elegant, practical, bizarre,
and corrupted. Keep style unified through Core Link ports, core displays,
nanobot assembly seams, scrap logic, energy conduits, and expressive sensors.

## Opening Sequence

The first experience should begin with the Core Link discovery and recovery.

Flow:

1. Player finds a damaged Core Link in a trash heap.
2. Player repairs/powers it enough to boot.
3. Core Link OS shows corrupted logs.
4. Owner identity is scrubbed.
5. Logs imply something valuable remains in void storage.
6. Player accesses storage.
7. Finds dormant AI core and nanobot container.
8. AI core is unresponsive and memory-damaged.
9. Core Link asks diagnostic/recovery questions.
10. Answers tune/recover the AI core personality matrix.
11. AI core wakes and syncs to the player.
12. Core Link accepts the player as operator.
13. Nanobots assemble the first rough chassis.
14. Tutorial mechanics unlock through repaired memory fragments.

The previous owner's identity should remain unknown at first. It was deliberately
scrubbed. Later, a powerful rival may recognize the Core Link as theirs.

## Tutorial Through Memory Recovery

The recovered AI core starts underpowered and tampered with. It remembers little
but has partial scavenging and defense protocols.

Tutorial should be delivered as memory returning after repairs, not as arbitrary
popups.

Example unlocks:

- diagnostics, mood, condition, Charge
- scrap repair
- component slots
- nanobot deployment
- void storage
- roaming/scavenging
- battle defense protocols later
- old owner logs later

## Watch Day Loop

The normal watch loop is a compact command dashboard/game scene.

The player checks:

- Scrap
- Charge
- bot mood
- bot condition
- repair needs
- upgrade needs later
- activity readiness

MVP actions:

- Charge / activity conversion or simulated charge
- Scan
- Repair
- Roam

Longer-term actions:

- battle
- hack/capture
- swap active bot
- deploy/retrieve
- craft/upgrade

## Scrap And Materials

Scrap exists at two levels:

1. Generic Scrap
2. Specific materials/components

The watch should show generic Scrap first. Deeper crafting can later use metal,
circuits, lenses, batteries, servos, chips, nanite gel, cables, sensors, memory
media, capacitors, plating, actuators, and display shards.

MVP:

- generic Scrap only unless a task explicitly needs materials.

## Roaming

Roaming is the passive progression path.

The player spends Charge to send the bot out. It returns later with rewards.

Roaming can yield:

- Scrap
- small components later
- experience/progress
- memory fragments later
- signals/encounters later

Roaming costs:

- Charge
- time
- possible condition wear later

## Battles And Hacking Later

Battles are deferred from MVP but important to the full concept.

Battle model:

- turn-based with move selection
- move count depends heavily on Memory
- moves can be learned naturally
- software move modules act like TMs

Move categories:

- physical
- hacking
- defense
- repair
- energy
- status/glitch
- movement/evasion
- utility/tactical

Post-battle capture/hack:

- target must be weakened first
- hacking is a short mini-game with skill and luck
- Core Link hacking tools can make it easier
- limited attempts before target rallies/escapes
- success can capture core, nanobots, components, or personality data

Captured AI cores can be:

- repaired and kept
- swapped into primary
- stored
- salvaged
- released
- traded/sold later
- used for software/memory/personality extraction
- combined into new personalities later

## Active Squad

Long-term active squad target is three bots:

1. Primary bot
2. Support bot
3. Roaming bot

The watch face should focus on one primary bot. MVP starts with one active bot,
but data decisions should avoid blocking a future three-bot squad.

## Core Link Upgrade Track

Core Link itself should have progression separate from bot growth.

Software upgrades later:

- hacking tools
- scan range
- diagnostics
- UI overlays
- battle analysis
- roam prediction
- storage indexing
- matrix tools
- firewall defense
- command macros
- low-power management

Hardware upgrades later:

- capacitor capacity
- charge retention
- signal range
- processor speed
- hologram quality
- storage access bandwidth
- nanobot control channels
- cable probe quality
- sensor package
- repair interface
- cooling/overclock tolerance

MVP can keep this as visible lore or a placeholder panel only if it does not
distract from the main loop.

## Moral Tension

The ethics are intentionally perspective-driven.

Some people hack bots for power, territory, or harm. Some hack to free cores
from bad firmware or corporate locks. Some partner with AI cores voluntarily.
Some just want scrap. Activists may view forced control as slavery; battlers may
view combat/capture as sport and status; corporations may view cores as property.

The game should not preach one answer early. Factions, quests, AI reactions, and
consequences can expose the tension later.

## Factions

Use these as first-draft faction anchors. Names and internal politics can evolve,
but each faction should create a distinct kind of pressure on AI cores, operators,
and the Core Link ecosystem.

- **The Foundries**: Corporate core makers controlling AI infrastructure.
- **Free Cores**: AI liberation networks fighting ownership and control.
- **Salvage Houses**: Repair families and scavengers surviving through reclaimed tech.
- **Circuit League**: Underground bot battlers chasing status, parts, credits.
- **Null Cartel**: Black-market brokers selling forbidden tech and identities.
- **The Custodians**: Containment activists protecting cores by imprisoning them.
- **The Backchannel**: Anonymous hackers sabotaging corporate tech monopolies.
- **The Last Hand**: Religious zealots opposing AI as false creation.
- **Old Owner's Network**: Hidden contacts tied to Core Link's erased past.

The Backchannel should feel like an anonymous underground hacker network. They
fight corporate monopolies by sabotaging infrastructure, rerouting deliveries,
leaking memory-wipe records, unlocking restricted tools, and monitoring abusive
systems. They work for ordinary people, but their actions can still create
collateral damage.

The Last Hand believes sentient AI is blasphemy: humanity playing god by making
minds without souls. Their public face can include shelters, sermons, charity,
and human-only repair guilds. Their darker edge includes destroying cores,
sabotaging relay towers, attacking AI-friendly repair shops, and deprogramming
operators. They should not be cartoon villains; their fear comes from real harms
caused by corporate AI and automation, but their answer is fanaticism.

## Relay, Contracts, And World Pulse

The watch keeps the player connected to the world through a lightweight network
surface. This should not be treated as long-form RPG questing on the watch. It is
short, readable, and decision-driven.

Story arrives through three channels:

- **Recovered Logs**: past events, AI memories, owner fragments, cache manifests.
- **Relay Messages**: direct packets from factions, contacts, markets, or unknown senders.
- **World Pulse**: ambient news showing how the world is moving.

Relay content can include:

- owner-locked messages meant for the previous Core Link operator
- dead drops
- faction broadcasts
- trade offers
- small contracts
- world news
- bot whispers sent directly to an AI core
- corporate notices
- black-market pings

Watch actions can create soft consequences, not hard main-story changes. The
watch can affect reputation, local news, side contacts, contract availability,
minor district conditions, and resource flows. The future 2D game should own
major canon progression.

Example:

```text
RELAY CONTRACT
sender: backchannel.node/unknown
request: reroute delivery manifest
need: 2 Charge, 1 Signal Key
reward: +Backchannel rep, rare move module
risk: Foundry trace
```

Example World Pulse:

```text
WORLD PULSE
Capacitor lockout protests spread through Dock Ward.
Unlicensed repair shops report restored power after anonymous firmware leak.
Foundry denies claims of forced device throttling.
```

## Markets, Crafting, And Trade

The watch can expose remote trade networks before the player physically reaches
equivalent services in the future 2D game. This should feel like operator network
access, not a normal shop menu.

Acquisition channels:

- **Crafting**: combine Scrap/components into parts, tanks, kits, chassis pieces, or modules.
- **Trade Networks**: remote Relay offers from factions, markets, or anonymous swaps.
- **Roam/Contracts**: dispatch or decision-based missions that return resources.
- **Exploration/Battles Later**: deeper acquisition in the future 2D game.

Crafting should not use watch-only crafting levels. If a recipe is available on
the watch, the future 2D game should be able to perform the same craft once the
player has equivalent tools, knowledge, or network access.

Energy tanks are useful as earned/traded items, but avoid selling filled Charge
directly. Charge should remain tied to movement/activity or development
simulation.

## Watch And Future 2D Game Relationship

The watch is the always-with-you companion and world-connection layer. It is not
the tiny version of the full RPG.

The future 2D game should own:

- exploration
- major missions
- battles
- faction story
- towns/zones
- major canon progression

The watch should own:

- companion check-ins
- movement-generated Charge
- light contracts
- world pulse
- recovered logs
- small trades
- repair/roam/scan decisions
- companion growth while away from PC or handheld

Future sync should be useful but not a hard design dependency for the watch MVP.
The watch should always have its own Core Link boot sequence. If the player
already knows Core Link from the 2D game, the watch can use a linked/operator
boot variant instead of pretending the device was discovered for the first time.

Possible boot variants:

- **Discovery Boot**: owner unknown, damaged cache, AI core recovery.
- **Linked Operator Boot**: operator recognized, companion sync, Relay enabled.
- **Degraded/Offline Boot**: local field mode, limited Relay, stored companion available.

Full import/export with the future 2D game can unlock after the player reaches,
repairs, or activates a Core Link Terminal or Relay Dock. This keeps both paths
coherent: watch-first players can bring history forward later, while game-first
players can enable the watch as a field extension.

## AI Core Body System

An AI core is a compact mind, workshop, and vault. It can contain internal
upgrade slots and a personal assembly cache.

Core internal systems:

- **Microfabricator Capsule**: injected into the core's center fabricator tube.
- **Core Cache**: the core's personal void-storage cube for body materials.
- **Material Loadout**: scrap/components assigned to that core's body.
- **Item Slots Later**: repair kits, move modules, firmware chips, tanks, keys, tools.

When an AI core deploys, its faceted shell splits open at the equator. A
perforated inner tube releases microfabricators. A small void aperture opens
above or behind the core, feeding stored scrap/components from the core's own
Core Cache. The AI projects a Matrix Scaffold, and the microfabricators assemble
the closest possible chassis around the core.

Deployment sequence:

```text
CORE DEPLOYMENT
shell: split
fabricator tube: open
capsule: MF-CIV/02
core cache: 8x8x8 active
material feed: scrap_mix_common
matrix scaffold: projected
assembly: started
```

The AI core can be worn or carried in a Core Cradle on a belt, harness, or case.
In the full RPG, an operator can throw or release a cradled core; by the time it
lands, the microfabricators can unfold and assemble the chassis around it if
Charge, material, and profile requirements are met.

The core should remain visibly present after assembly. Its luminous faceplate or
Core Aperture remains exposed somewhere on the chassis, often like a flat
reactor-style light. When the AI speaks, the faceplate brightens and dims with
its voice. Mood, damage, low power, trust, and corruption can change its color,
waveform, flicker, or scanline pattern.

## Void Grid And Core Cache

Void storage is not magic inventory. Treat it as corporate physical-matter
storage accessed through network license keys.

The **Void Grid** is an offshore, heavily surveilled storage network operated by
corporations. Storage locations are real, remote, automated, and guarded. A
Cache Key grants digital access to a licensed storage cube such as `8x8x8` or
`16x16x16`.

Most AI cores are manufactured with personal void-storage access for body
materials and maintenance. The core's cache size, license status, and stored
material quality determine what kind of chassis it can assemble.

Hackers frequently attack the Void Grid to steal access, squat storage, reroute
ownership, or obtain unpaid cache space. This makes storage political and
economic: corporations charge rent for physical existence, and factions fight
over who gets to own body materials.

Useful terms:

- **Void Grid**: corporate physical-matter storage network.
- **Core Cache**: an AI core's personal body-material cube.
- **Cache Key**: license credential for storage access.
- **Material Loadout**: assigned body materials inside a Core Cache.
- **Matrix Scaffold**: holographic assembly blueprint from AI/Core Link.
- **Microfabricator Capsule**: replaceable fabricator swarm module.
- **Core Cradle**: safe carry/charging housing for deployable cores.

## Microfabricators

Use **microfabricators** as the preferred technical term. People may casually say
nanobots, but the Core Link system should treat them as constrained fabrication
tools, not universal matter magic.

Microfabricators:

- assemble and deconstruct compatible bot chassis
- repair and reshape inorganic materials
- require Charge
- require known material profiles
- require chassis patterns or Matrix Scaffolds
- are limited by capsule quality, swarm density, and control bandwidth
- are safety-locked against organic substrates in normal civilian/operator use

They do not understand all matter by default. They need material profiles and
operation permissions: composition, stress behavior, safe cut points, assembly
tolerances, authorization, and permitted operations.

Medical microfabricators can exist, but they are a separate regulated class:
organic-safe, operation-limited, clinic-controlled, biometric-authorized, and
usually unable to perform general hostile disassembly.

Military or illegal microfabricators may bypass safety systems, but they are
rare, traceable, unstable, and treated as story-level threats.

## Chassis Identity And Reconfiguration

An AI core's body is its current circumstance, not its species. Healthy cores can
have clear chassis preferences. Body choice can express work, status, culture,
personality, faction, trauma, aesthetics, combat style, or available materials.

The final chassis is shaped by:

- AI intent
- Matrix Scaffold translation
- microfabricator precision
- material quality
- available profiles
- Charge and time

Some rare mimic/reconfiguration cores understand the world by imitating it. They
can observe movement, silhouette, armor, weapons, posture, or behavior and
generate new chassis profiles from that data.

Mid-battle chassis shifting should be rare, expensive, and strategic:

- consumes Charge
- creates heat or stability strain
- may expose the core during transition
- requires compatible stored materials
- requires high-quality microfabricators
- depends on scanned or learned profiles

Specialists should remain stronger at their specialty. Mimic/reconfiguration
cores are flexible and unpredictable, but costly to operate.

Example:

```text
MIMIC FRAME SHIFT
profile: BULWARK SHELL
cost: 18 Charge
risk: +12 heat
core exposure: 1 turn
```

## MVP Guardrails

For current worker tasks:

- Native Wear OS only.
- No WebView/HTML/CSS/JS prototype substitution.
- Use `Core Link` for player-facing text.
- Do not call the device a rig in player-facing MVP text.
- Primary surface should be a visual game scene, not static metric cards.
- The companion should be visible and animated.
- Keep Charge/Scrap/Condition compact.
- Keep interactions light and optional.
- Do not implement paid Charge.
- Do not implement harsh permanent dead-core loss.
- Keep one starter AI core and one active bot.
- Battles, capture, store, and full phone RPG are deferred.
