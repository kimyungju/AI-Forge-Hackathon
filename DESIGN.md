# 60's Pulse Design System

## 1. Atmosphere & Identity

60's Pulse feels like an adversarial newsroom war room: editorial, urgent, and data-dense without becoming neon cyberpunk. The signature is the simulated broadsheet: warm newsprint surfaces, black ink, a restrained alarm red, and agent portraits that behave like evidence markers rather than decorative avatars.

## 2. Color

### Palette

| Role | Token | Light | Dark | Usage |
|------|-------|-------|------|-------|
| Surface/page | `--paper` | `#FBFAF6` | N/A | Main newsprint background |
| Surface/panel | `--paper-2` | `#F4F1E8` | N/A | Cards, badges, inputs |
| Surface/well | `--paper-3` | `#EAE6D9` | N/A | Meter tracks, muted chips |
| Text/primary | `--ink` | `#1A1610` | N/A | Headlines, body, outlines |
| Text/secondary | `--ink-soft` | `#5B5443` | N/A | Metadata, captions |
| Text/faint | `--ink-faint` | `#908975` | N/A | Disabled and quiet labels |
| Border/default | `--rule` | `rgba(26, 22, 16, 0.16)` | N/A | Dividers, panel outlines |
| Border/subtle | `--rule-soft` | `rgba(26, 22, 16, 0.08)` | N/A | Soft meter borders |
| Severity/calm | `--calm` | `#9DB0A9` | N/A | Low-risk agents |
| Severity/rising | `--rising` | `#CBB24E` | N/A | Mild and rising risk |
| Severity/severe | `--severe` | `#C2622C` | N/A | Serious objections |
| Severity/blast | `--blast` | `#A6201A` | N/A | Blast score, delay alarm |
| Status/go | `--go` | `#2E6B4F` | N/A | Launch verdict and positive status |
| Status/revise | `--revise` | `#C18A1B` | N/A | Revise verdict and copy fixes |
| Accent/alarm | `--accent` | `#A6201A` | N/A | Primary action and focus accents |

### Rules

- Keep the palette warm and editorial. Avoid neon, purple-blue SaaS gradients, and decorative color.
- Red is for real alarm states or primary actions only.
- Severity colors must stay legible on `--paper` and inside agent cells.

## 3. Typography

### Scale

| Level | Size | Weight | Line Height | Tracking | Usage |
|-------|------|--------|-------------|----------|-------|
| Display | `clamp(110px, 17vw, 232px)` | 900 italic | 0.8 | `-0.02em` | Blast score |
| H1 | `clamp(34px, 5.5vw, 58px)` | 900 italic | 1 | `-0.02em` | Input title |
| H2 | `clamp(22px, 3.1vw, 40px)` | 800 | 1.06 | `-0.01em` | Future headline |
| H3 | `19px` | 800 | 1.3 | 0 | Column titles |
| Body | `16px` | 400 | 1.5 | 0 | Base page text |
| Body/sm | `12px-14px` | 400-600 | 1.4-1.55 | `0.02em-0.08em` | Metadata and captions |
| Overline | `10px-12px` | 600-700 | 1.3 | `0.16em-0.3em` | Kicker labels |

### Font Stack

- Display: `'Fraunces', Georgia, 'Times New Roman', serif`
- Mono/data: `'IBM Plex Mono', 'SFMono-Regular', Consolas, monospace`
- Nameplate: `'UnifrakturCook', 'Fraunces', serif`

### Rules

- Serif carries editorial judgment; mono carries evidence and controls.
- Body and controls stay at 12px or larger.
- Letter spacing is used only for overlines and mono metadata, never as a broad decorative effect.

## 4. Spacing & Layout

### Base Unit

All spacing derives from 4px multiples. The main page pad is `--pad: clamp(16px, 2.4vw, 34px)`.

| Token | Value | Usage |
|-------|-------|-------|
| `--space-1` | `4px` | Micro gaps |
| `--space-2` | `8px` | Inline controls and chip gaps |
| `--space-3` | `12px` | Compact card padding |
| `--space-4` | `16px` | Standard card padding |
| `--space-6` | `24px` | Grid gaps and section inner rhythm |
| `--space-8` | `32px` | Major section separation |

### Grid

- Max content width: `1340px`
- Desktop dashboard: two-column fold top and three-column forensics grid.
- Breakpoints: collapse at `980px`; mobile grids increase density without horizontal scroll.

### Rules

- Keep cards shallow. Use borders and tonal shifts, not nested floating card stacks.
- Fixed-format grids and meters need stable dimensions so animation does not shift layout.

## 5. Components

### Agent Tile

- Structure: `button.tile.agent-avatar` with portrait spans and initials.
- Variants: persona circle, lens rounded square, stakeholder square, abstain disabled.
- Spacing: square aspect ratio, 6px grid gap on dashboard, 8px in run view.
- States: default, hover scale, focus outline, disabled abstain.
- Accessibility: button semantics, `aria-label`, disabled abstain tiles removed from tab order.
- Motion: ignite animation on entry; transform-only hover.

### Timeline Bar

- Structure: `button.tl-bar` containing percentage, bar, and timestamp.
- Variants: peak marker and standard bar.
- States: default, hover brightness, focus outline.
- Accessibility: `aria-label` describes time range and trigger percentage.
- Motion: height transition on the child `.bar`.

### Quote Card

- Structure: fixed dialog with close button and DOM-rendered text nodes.
- States: open, hidden, keyboard close via Escape.
- Accessibility: dialog role with modal semantics and labelled close button.

## 6. Motion & Interaction

### Timing

| Type | Duration | Easing | Usage |
|------|----------|--------|-------|
| Micro | `0.1s-0.16s` | `ease` | Button and card hover |
| Standard | `0.35s-0.42s` | `cubic-bezier(.2,.8,.2,1)` | Agent entry |
| Emphasis | `0.7s-1.1s` | `cubic-bezier(.2,.7,.2,1)` | Reveal sections, meters |
| Ticker | `34s` | `linear` | Sponsor ticker |

### Rules

- Animate `transform`, `opacity`, `filter`, and meter dimensions only where the existing design already uses them.
- Respect `prefers-reduced-motion` for reveal animations.
- Every interactive control has a visible focus state.

## 7. Depth & Surface

### Strategy

Mixed, but restrained: editorial borders plus tonal surfaces, with shadow reserved for modal quote cards and elevated input composer.

| Level | Value | Usage |
|-------|-------|-------|
| Border/default | `1px solid var(--rule)` | Cards, sections, badges |
| Border/strong | `3px solid var(--ink)` | Masthead and fold rules |
| Shadow/subtle | `0 18px 50px rgba(26,22,16,0.1)` | Composer |
| Shadow/modal | `0 40px 120px rgba(26,22,16,0.3)` | Quote card |

### Rules

- Do not add decorative shadows to repeated cards.
- Keep the modal shadow strong enough to separate it from the broadsheet without adding an overlay.
