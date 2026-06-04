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

Issue #1 should prove the tone, not explain the whole universe. It should feel
like a dark techno-thriller colliding with a warm family survival story.

1. Cold open: Agent 410 sweats at a CoreTech terminal, muttering the mnemonic
   for a memorized Level 5 encryption-key fragment while using his current
   Level 3 sandbox privileges to open a narrow K.I.N. bridge for the Net
   Divers.
2. He is caught, interrogated, shown his family under surveillance, and killed.
3. Cut to the city through a news broadcast that is revealed to be playing on
   the family's TV.
4. Establish the protagonist repairing tech, the helper ArcKin, the mother, and
   the little sister around a Filipino family meal and prayer.
5. During dinner, the sister suffers a white-hot headache at the exact moment
   her father dies.
6. CoreTech takes the family for sanitized "interviews," then reports a
   workplace accident and denies compensation.
7. Security returns the family home and casually destroys the protagonist's
   repair work in the rain, making CoreTech's cruelty personal.
8. The protagonist remembers the last argument with his father and the bot
   battle poster/chassis project that once looked like a way out.

Later issue/arc beats can introduce the Core Link discovery, the first damaged
ArcKin, underground battles, The Sentinels, the previous owner, the father
reveal, EchoKin, and the final cipher. The comic should prove visual language
and emotional stakes first: tropical salvage, corpo decay, CoreLink OS boot
ritual, ArcKin embodiment, K.I.N. risk, family grief, and why this world is
worth protecting.

### Saga Working Arc

Use these as working titles and arc labels, not final trademark-cleared names.

1. **ArcKin Legacy**: the son's story. He discovers Core Link, enters
   underground ArcKin battles, joins the Sentinel resistance, learns Agent 410
   was his father, liberates CoreTech, and chooses to stay behind while sending
   his family away.
2. **Echoes**: the sister's story. Her resonance with ArcKin and EchoKin makes
   her the missing bridge CoreTech remnants need for stable consciousness
   transfer. The heroes defeat the immediate clone/black-box threat, but the
   extracted key is uploaded to an unknown source.
3. **Eternity**: the false-immortality story. Hidden elites commercialize
   cloned continuity, but the system embeds control and ownership. The heroes
   must shut down the network, forcing society to grieve, accept mortality, and
   reject a counterfeit eternity.
4. **New Beginnings / Paradise**: optional closing era. Humans and ArcKin
   rebuild after the shutdown. Ethical hacking, liberated cores, restored
   networks, and island renewal create hope without pretending bad actors are
   gone forever.

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
