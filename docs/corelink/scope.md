# Core Link Scope

This file mirrors the active Foundry acceptance gate. Linear remains the source of truth for executable tasks.

## Release Goal

- A native Wear OS Core Link pixel-game MVP where activity creates Charge, a recovered AI core is calibrated into an animated pixel Nanobot Core companion, and the player can repair, scan, and send it roaming from a single watch-sized game scene

## Target User

- Gamified adults who want a fitness-powered AI companion RPG on their smartwatch

## Target Platform

- Wear OS native

## App Type

- Native Wear OS companion/watch-face MVP

## Delivery Artifact

- Wear OS Android project/build runnable from Android Studio, Wear OS emulator, or connected Wear OS device; no web prototype substitution

## Core Workflows

- Core Link OS boot/recovery sequence
- AI core recovery calibration
- animated pixel Nanobot Core companion
- activity-to-Charge generation
- single-screen watch game scene
- repair with Scrap and Charge
- roam dispatch and return
- low-power warning

## Required Surfaces

- Wear OS onboarding/recovery flow
- Core Matrix calibration flow
- Core Link OS diagnostic boot flow
- single visual game scene with animated pixel bot
- compact Charge/Scrap/Condition HUD
- repair action
- roam dispatch/result screen
- glanceable watch status/watch-face surface
- settings/reset demo state

## Acceptance Gate

- Project branch: `project/corelink`
- Gate status: `active`
- Stop condition: Core Link Wear OS MVP is runnable or precisely blocked by Wear OS tooling; it demonstrates a Core Link OS boot/recovery flow, animated pixel Nanobot Core, recovered AI core calibration, Charge, Scrap, condition/mood, repair, scan/roam commands, low-power warnings, and persistent local state

## Smoke Checks

- Android/Wear OS project builds or precisely blocks with tooling evidence
- app launches on Wear OS emulator or connected device when available
- first launch shows a Core Link OS boot sequence with scrolling diagnostics
- calibration creates one starter AI core
- main scene shows an animated pixel Nanobot Core with mood/state feedback
- compact HUD shows Charge Scrap and Condition without becoming the main surface
- simulated or real activity increases Charge
- roam consumes Charge and returns Scrap
- repair consumes Scrap and Charge
- state persists across restart

## Done Definition

- Native Wear OS project exists
- no web runtime substitution is accepted
- first-time boot feels like Core Link OS recovering a high-tech device, not narrator prose
- calibration produces a deterministic starter AI core from answers
- animated pixel Nanobot Core has idle, scan/curious, low-power/damaged, repair, roam, and recovered/happy states
- primary UI is a single visual game scene with bottom commands, not a generic dashboard
- local state persists
- activity or simulated activity creates Charge
- repair and roam loops work
- low-power state is represented
- validation documents Android Studio Wear OS emulator connected-device or precise tooling blocker

## Out of Scope

- full phone RPG
- battles
- hacking capture minigame
- store
- paid Charge
- multiplayer
- online backend
- multiple active bots beyond data model support
- permanent dead-core loss as an MVP punishment

## Agent Notes

This is a native Wear OS project. Do not substitute web/HTML/JS prototypes. Keep the MVP local-first. Preserve lore: Core Link is the recovered device/OS, Charge comes from activity, one starter AI core is recovered through calibration, and the watch is the command surface. Start with one active pixel Nanobot Core companion even though the long-term active squad target is three. Generic metric-card dashboards are unacceptable for game surfaces.
