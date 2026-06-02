<!--
Portions of this file are derived from pbakaus/impeccable
(https://github.com/pbakaus/impeccable), Apache License 2.0.
Snapshot 2026-06-02.

See plugins/frontend/NOTICE.md for the full upstream attribution chain.
For motion mechanics (durations, easing curves, staggering, reduced-motion),
see motion-design.md. This file covers WHERE and WHEN to add delight.
-->

# Delight & Micro-interactions

Delight is the personality and unexpected polish that turns a functional interface into one people remember and tell others about. The core discipline: add it only where the moment earns it. Delight pushed everywhere reads as noise, and reliability carries the rest of the experience.

## Where delight belongs

Product surfaces earn delight at *specific moments*, not on every page: completion, first-time actions, error recovery, milestone crossings. Brand surfaces can distribute it more widely across copy voice, transitions, and discovery rewards. Match the register to the domain (a banking app is not a gaming app).

## Principles

- **Amplifies, never blocks**: delight moments stay under ~1 second, never delay core functionality, and stay skippable or subtle.
- **Rewards discovery**: hide some details for curious users to find; do not announce every moment.
- **Appropriate to state**: celebrate success, empathize with errors. Do not be playful during a critical error.
- **Compounds over time**: vary responses so the 100th encounter still feels fresh; reveal deeper layers with continued use.

## Micro-interaction examples

```css
/* Satisfying press: dip on active, lift on hover */
.button { transition: transform 0.1s, box-shadow 0.1s; }
.button:active { transform: translateY(2px); box-shadow: 0 2px 4px rgba(0,0,0,0.2); }
.button:hover {
  transform: translateY(-2px);
  transition: transform 0.2s cubic-bezier(0.25, 1, 0.5, 1); /* ease-out-quart */
}
```

Good candidates: icons that animate on hover, checkboxes that pulse-scale when checked, inputs that animate on focus, auto-grow textareas, toggle switches with a smooth slide and color transition (plus haptic feedback on mobile). For drag-and-drop, lift on grab (shadow + scale), snap on drop, and offer an undo toast.

## Personality in copy

Match copy personality to the brand (banks should be warm, not wacky). The lever is replacing flat system strings with voice:

- Error: "This page is playing hide and seek (and winning)." instead of bare "Error 404".
- Empty: "Your canvas awaits. Create something." instead of "No projects".
- Label/tooltip: "Send to void" for a playful delete; "Rescue me" for help.

## Loading & waiting states

Make waiting engaging: rotating messages, progress bars with personality, fun facts or tips, encouraging copy. Write messages specific to what the product actually does:

```
"Crunching your latest numbers..."
"Syncing with your team's changes..."
"Preparing your dashboard..."
```

**The AI-slop trap**: avoid cliched loading copy like "Herding pixels", "Teaching robots to dance", "Consulting the magic 8-ball", "Counting backwards from infinity". These read as instantly machine-generated. Specificity to the product is what makes the line land.

## Celebration & milestones

Confetti for major milestones, a drawn checkmark for completions, a progress bar that celebrates at 100%, "achievement unlocked" notifications, and personalized messages ("You published your 10th article!"). First-time actions and streaks deserve special treatment.

## Visual personality

Custom illustrations for empty/error/success states beat stock icons. A custom icon set with subtle hover motion reinforces brand. Background texture (subtle particles, gradient mesh, parallax depth, time-of-day themes) adds richness when it stays in the background.

## Sound design

Subtle audio cues when appropriate: a satisfying success "ding", an empathetic (not harsh) error sound, distinctive notification tones. Respect system sound settings, provide a mute option, keep volumes quiet, and never play on every interaction (sound fatigue is real).

## Easter eggs & hidden delights

Konami-code themes, hidden keyboard shortcuts, hover reveals on logos, alt-text jokes (screen-reader users get them too), console messages for developers. Seasonal and time-based touches (subtle holiday themes, dark at night) reward repeat visits.

## Implementation libraries

- **Animation**: Framer Motion (React), GSAP (universal), Lottie (After Effects exports), canvas-confetti (celebrations).
- **Sound**: Howler.js, use-sound (React hook).
- **Physics**: React Spring, Popmotion.

File size matters: compress images, optimize animations, and lazy-load delight features.

---

**Avoid**: Delaying core functionality for delight. Forcing users through unskippable moments. Using delight to mask poor UX. Making *every* interaction delightful (special moments must stay special). Ignoring `prefers-reduced-motion` and screen readers. Being tonally inappropriate for the context.
