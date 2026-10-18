# Simple Mode website implementation plan

Status: approved scope from the user's request; implementation in progress.
Base: `0f998df29184274d9c60317d2c8973c5a38e4d02`.
Workspace: `/home/jimmy/.paseo/worktrees/13nkmqul/simple-mode-web`.

## Product contract

Deliver a Korean beginner setup website using Next.js App Router, TypeScript and Zustand, with production deployment on Vercel. Preserve the existing research and Python reference implementation. The website is an actionable guide hub: it links real signup, billing, key consoles and installers, provides copyable setup/configuration and downloadable resources, and records the user's own checklist. It does not imply that clicking a checkbox verifies an installation or account.

Simple Mode starts with Codex. The broader four independent host OS / three original agent goal remains unchanged; unsupported and unverified mobile local actions remain visible with reasons. Browser detection is a suggested platform, with explicit manual override. It cannot detect installed dependencies or credentials.

Required coverage: Codex/ChatGPT and API billing; OpenRouter; HY4 Preview, DeepSeek V4.1 Flash, Seedance 2.5, economical video, image generation and Jev; Node/npm, Python, Next.js/Zustand, Flutter/MVVM, domain skills; Supabase/Airtable/Firebase; n8n Cloud; Vercel; GitHub; Play/App Store; Threads/Instagram; Gmail/YouTube/Maps/Drive/Sheets/Slides; Unity; Higgsfield, Shotstack and ElevenLabs; agent-browser/Playwright comparison and Tencent BrowserSkill. Model IDs and modalities require current primary-source evidence.

Signup, documentation, web-console navigation and local execution are separate actions. A Windows visitor may open Apple's enrollment site, but local iOS build needs macOS/Xcode. Mobile visitors may use web cloud services; local desktop SDK/editor actions are disabled. Unknown OS fails closed for local execution. Conditional actions show their prerequisites; unverified install actions are disabled, with research guidance still readable.

Every service guide includes an authentic public-page screenshot with source/date/caption. Logged-in private console screens are not fabricated. Clearly label public documentation screenshots and steps requiring the user's own account. Never collect API keys in website forms or persist secrets in Zustand/localStorage.

## Design

Use ui-ux-pro-max design-system and Next.js guidance. Adopt a calm editorial dashboard: warm ivory, deep ink, emerald/mint accents, high-contrast Korean typography, generous spacing, SVG icons and a three-step onboarding funnel. Avoid blur-heavy effects where readability suffers. A licensed HTML dashboard reference will inform sidebar/cards/step layouts; record exact reference and license. Desktop sidebar, mobile compact navigation; responsive at 375/768/1024/1440 px, visible keyboard focus, 44 px targets, reduced-motion support, disabled reasons visible without hover.

Routes: `/` personal start; `/catalog` searchable guide library; `/guides/[slug]` detailed setup; `/models` role-based model configuration; `/compatibility` action-level matrix; `/browser-tools` researched browser stack. Use one shared typed catalog for cards, guides, counts, support and external actions. No fake metrics, connected states or unavailable downloads.

## Ownership and sequence

1. Master freezes types, product rules, worktree and design; research workers verify models, browser stack, OS support/template.
2. UI implementer owns `web/package*.json`, `web/*config*`, `web/src/app`, `web/src/components`, `web/src/store`, `web/tests/ui`, fonts and app icons. Installs dependencies using Node 24. Consumes the shared contract; does not write data/lib contract.
3. Catalog implementer owns `web/src/data`, `web/src/lib/capabilities.ts`, `web/src/lib/platform.ts`, unit tests and research evidence. Populate all requirements, guide steps, official links and command boundaries. No UI edits or dependency mutations.
4. Asset/setup implementer owns `web/public/guides`, `web/public/downloads`, capture scripts and `docs/simple-mode-guides.md`. Capture real public screenshots; prepare Supabase admin SQL lifecycle and useful model/setup downloads. No production account mutation or paid generation calls.
5. Separate reviewer checks contract, implementation, secret boundaries and disabled actions. Master verifies actual tests/build, visual desktop/mobile behavior and downloadable assets; fixes are assigned to owners. Strongest final reviewer checks the integrated branch.
6. Commit/push feature branch, create a reviewable GitHub PR, deploy the dedicated new Vercel project and verify live routes. No changes to unrelated Vercel projects.

## Validation

- Capability tests cover Windows/macOS/Android/iOS/iPad desktop UA/Linux/unknown, manual override, desktop tools, cloud actions and the iOS build exception.
- Catalog tests cover IDs, internal references, required service coverage, HTTPS external links, source and screenshot metadata, models and supported/disabled rules.
- Browser tests cover search, category filter, guide navigation, platform selection and persistence, checklist/reset, disabled click behavior, download/copy and responsive layout.
- Typecheck, lint, unit tests, production build, browser visual checks and critical live deployment checks. Existing Python tests run once as required by AGENTS; report pre-existing environment-dependent failures separately if unchanged.
- Record commands/counts, screenshots, commits and deployment URL. Fixture/browser tests are not evidence of mobile agent installation, paid provider access or account authentication.

## Scope boundaries

No customer signup, billing transaction, key creation, account posting or private console screenshots in this delivery. The user performs account-bound actions via explicit links and illustrated guides. Site creation and Vercel deployment are authorized. Legacy CLI defects only need changes if the website relies on that path; otherwise clearly keep experimental CLI separate from the guide website.
