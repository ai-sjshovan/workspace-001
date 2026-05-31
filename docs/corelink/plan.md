# Core Link Plan

Use this file for high-level sequencing. Linear remains the source of truth for executable tasks.

## Release 1 Sequence

Before pushing deeper into game production, consider a comic-first lore
validation path. The comic can ground tone, characters, ArcKin rules, K.I.N.
crisis, CoreLink OS visuals, EchoKin, and the tropical/corpo setting before the
watch game and future 2D game need to carry all of that through mechanics.

### Comic-First Lore Path

Treat the first public comic as canon foundation, not side content.

Use comics/anime to carry the heaviest story depth. The watch and game should
stay playable, approachable, and open-ended: ArcKin bonding, contracts,
competitions, repairs, scavenging, travel, and neighborhood adventures first.
Main conspiracy beats should appear as major heartbeats and grounded dialogue,
not constant plot pressure. Players who want the full father/CoreTech/K.I.N.
truth can follow the comics.

Working first issue:

**CoreLink: Broken Kernel #1**

Issue #1 should contain the full first arc as scenes/beats, not six separate
issues:

1. Cold open: Agent 410 sweats at a CoreTech terminal, using elevated
   privileges and an underground key to access a forbidden K.I.N. route.
2. Scavenger life in a tropical metro/salvage district.
3. The protagonist finds a damaged CoreLink in a trash heap.
4. CoreLink OS boots and discovers a dormant ARC plus strange stored resources.
5. A local K.I.N. breach causes neighborhood danger or exposes corpo pressure.
6. The first ArcKin bond forms through recovery, trust, and improvised repair.
7. An EchoKin encounter reveals an unfinished warning, blueprint, route, or
   hidden truth that forces the protagonist to choose whether to hide, sell, or
   use the CoreLink.

The comic should prove visual language and emotional stakes first: tropical
salvage, corpo decay, CoreLink OS boot ritual, ArcKin embodiment, K.I.N. risk,
EchoKin tragedy, and why this world is worth protecting.

## Watch MVP Sequence

1. Establish a native Wear OS Android scaffold and run path.
2. Implement deterministic AI core calibration and local state persistence.
3. Rework the watch surface into a single Core Link OS game scene with animated pixel Nanobot Core, compact HUD, and bottom command buttons.
4. Add simulated or real activity-to-Charge generation.
5. Implement repair and roam loops.
6. Add low-power state handling and persistence validation.

## Validation Policy

- CoreLink is native Wear OS. Do not accept WebView, HTML, CSS, JavaScript, or
  browser-only substitutes.
- `lore-product-brief.md` is required product/lore context for Core Link design,
  onboarding, mechanics, and QA decisions.
- `watch-ui-and-systems.md` is required context for watch UI, Relay, contracts,
  boot variants, and short-session interaction design.
- The focused Core Link briefs under `knowledge/projects/corelink/` should be
  used to avoid flattening the product into generic watch counters or RPG menus.
- Core Link game surfaces must not be accepted as static metric cards or plain
  dashboard panels. The player should see the bot, feel the OS boot/recovery
  fiction, and receive visual feedback for commands.
- Early scaffold/run-path tasks may be accepted when they create real native
  Android/Wear OS project files and document precise local tooling blockers.
- Full release acceptance still requires the MVP workflows to pass or be
  precisely blocked by Wear OS tooling.
