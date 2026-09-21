---
name: awesome-design-md
description: Look up and apply a ready-made DESIGN.md design language for a named brand or product (Vercel, Linear, Notion, Stripe, Apple, Raycast, Figma, Tesla, … 74 in total). Use when the user wants UI to "look like <brand>", asks for a specific visual style, wants design tokens / type scale / component specs from a reference product, or wants a DESIGN.md copied into a project. Do not invent tokens when an indexed DESIGN.md exists. Do not overwrite a project that already has its own DESIGN.md or locked design system without explicit confirmation.
---

# Awesome DESIGN.md

A local snapshot of [VoltAgent/awesome-design-md](https://github.com/VoltAgent/awesome-design-md) — 74 ready-to-use `DESIGN.md` files, each an analysis of one real product's design language.

`DESIGN.md` is the design-system counterpart of `AGENTS.md` (a concept from Google Stitch): a plain markdown file an AI agent reads to generate visually consistent UI. No Figma export, no JSON schema, no tooling — just a markdown file.

| File | Who reads it | What it defines |
|---|---|---|
| `AGENTS.md` | Coding agents | How to build the project |
| `DESIGN.md` | Design agents | How the project should look and feel |

## Layout

```
~/.codebuddy/skills/awesome-design-md/
└── design-md/
    ├── vercel/DESIGN.md
    ├── linear.app/DESIGN.md
    └── … 74 brands in total
```

Read a file with `read_file`; find one by name with `search_file` (`design-md/*/DESIGN.md`). Total ~2.1 MB, largest file ~43 KB (`mintlify`), smallest ~4 KB (`kraken`).

## Index

**AI & LLM** — `claude` warm terracotta accent, editorial · `cohere` vibrant gradients, data-rich dashboard · `elevenlabs` dark cinematic, audio-waveform · `minimax` bold dark with neon accents · `mistral.ai` French minimalism, purple-toned · `ollama` terminal-first monochrome · `opencode.ai` developer dark theme · `replicate` clean white canvas, code-forward · `runwayml` cinematic dark heroes, paper-white reading bands · `together.ai` technical blueprint style · `voltagent` void-black canvas, emerald accent · `x.ai` stark monochrome futurism

**Developer tools & IDEs** — `cursor` sleek dark, gradient accents · `expo` dark, tight letter-spacing · `lovable` playful gradients · `raycast` dark chrome, vibrant gradient accents · `superhuman` premium dark, purple glow · `vercel` black-and-ink precision, Geist font · `warp` dark IDE-like, block-based terminal

**Backend, database & DevOps** — `clickhouse` yellow-accented technical docs · `composio` modern dark, colorful integration icons · `hashicorp` enterprise black and white · `mongodb` green leaf, documentation focus · `posthog` playful hedgehog, developer dark · `sanity` dark-first editorial, 112px display type · `sentry` data-dense dark dashboard, pink-purple accent · `supabase` dark emerald, code-first

**Productivity & SaaS** — `cal` clean neutral, developer simplicity · `intercom` friendly blue, conversational · `linear.app` ultra-minimal, precise, purple accent · `mintlify` clean green-accented, reading-optimized · `notion` warm minimalism, serif headings · `resend` minimal dark, monospace accents · `zapier` warm orange, illustration-driven

**Design & creative tools** — `airtable` colorful structured data · `clay` organic shapes, soft gradients · `figma` vibrant multi-color, playful professional · `framer` bold black and blue, motion-first · `miro` bright yellow, infinite canvas · `webflow` blue-accented polished marketing

**Fintech & crypto** — `binance` Binance Yellow on monochrome · `coinbase` clean institutional blue · `kraken` purple-accented dark, data-dense · `mastercard` warm cream canvas, orbital pills · `revolut` sleek dark, gradient cards · `stripe` signature purple gradients, weight-300 · `wise` bright green, friendly and clear

**E-commerce & retail** — `airbnb` warm coral, photography-driven, rounded · `meta` photography-first, binary light/dark, Meta Blue · `nike` monochrome UI, massive uppercase Futura · `shopify` dark cinematic, neon green · `starbucks` four-tier earth-green, warm cream

**Media & consumer tech** — `apple` premium white space, SF Pro · `hp` pure white, Electric Blue signal CTA · `ibm` Carbon design system, structured blue · `nvidia` green-black technical energy · `pinterest` red accent, masonry grid · `playstation` three-surface channel layout, cyan hover-scale · `spacex` stark black and white, full-bleed · `spotify` vibrant green on dark, album-art-driven · `theverge` acid-mint and ultraviolet, Manuka type · `uber` bold black and white, urban · `vodafone` monumental uppercase, Vodafone Red · `wired` paper-white broadsheet, ink-blue links

**Automotive** — `bmw` dark premium, German precision · `bmw-m` motorsport contrast, M color accents · `bugatti` cinema-black, monumental display type · `ferrari` chiaroscuro editorial, Ferrari Red · `lamborghini` true black cathedral, gold accent · `renault` aurora gradients, zero-radius buttons · `tesla` radical subtraction, cinematic full-viewport

**Retro web** — `dell-1996` catalog-era enterprise, flat ribbon cards, GIF stickers · `nintendo-2001` Y2K console chrome, beveled metal panels

**Other** — `slack` (present in the snapshot, not categorised upstream)

## File format

Every `DESIGN.md` opens with YAML frontmatter —

```yaml
---
version: alpha
name: Vercel-Inspired-design-analysis
description: <one-paragraph characterisation of the design language>
colors:
  primary: "#171717"
  canvas: "#ffffff"
  ...
typography: ...
---
```

— followed by up to nine `##` sections: `Visual Theme & Atmosphere`, `Color Palette & Roles`, `Typography Rules`, `Component Stylings`, `Layout Principles`, `Depth & Elevation`, `Do's and Don'ts`, `Responsive Behavior`, `Agent Prompt Guide` (actual section set varies per file; `vercel` has 8).

## Workflow

1. **Resolve the brand** from the index above → `design-md/<brand>/DESIGN.md`. If the user names a product not in the index, say so; do not substitute a "close enough" brand silently.
2. **Read the file in full** before generating anything. The frontmatter tokens and the section bodies together are the spec — a partial read produces an off-brand result.
3. **Choose the application mode and state which one you used:**
   - *Reference mode* — keep the file where it is and translate its tokens/rules into the target stack (the usual choice for an existing codebase).
   - *Copy mode* — copy the file to the target project root as `DESIGN.md`, as the upstream README describes ("copy a site's DESIGN.md into your project root").
4. **Check for a conflict before writing anything into a project.** If the target already has a `DESIGN.md`, a design-token module, or a documented visual system, do not overwrite it: report the conflict and the two candidate directions, then wait for the user.
5. **One brand at a time.** Do not blend two DESIGN.md files unless explicitly asked; the result loses the coherence that makes the document useful.
6. **Map, don't paste.** Real values still have to be adapted to the target stack (class names, CSS variables, component library themes). Do not leave reference-only values such as brand-specific font names in place of loaded fonts.

## Boundaries

- This is a **read-only reference snapshot**. Do not edit files under `design-md/`.
- Files are **"inspired interpretations"** (`version: alpha`) with tokens extracted from publicly visible CSS. They are not official brand style guides and carry no brand endorsement.
- Upstream also publishes `preview.html` / `preview-dark.html` catalogs and per-brand `README.md` stubs; neither is included here — the stubs only point at `getdesign.md`, and the HTML previews are not part of the published tree.
- Use `create-design-md` instead when the task is to **document a design language that does not have one yet** (from a repo or a live URL). This skill only supplies existing, third-party design languages.
- Licence: MIT (upstream). See the repository for the full notice.
