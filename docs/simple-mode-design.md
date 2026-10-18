# Simple Mode design and platform contract

Decision date: 2026-10-18. These decisions implement the user's explicit Next.js, Zustand, ui-ux-pro-max and Vercel request.

## Experience

The entry point asks what the visitor wants to make, suggests a device platform, and gives three concrete stages: prepare the agent, connect the chosen services, and make a first result. The catalog remains accessible for users who already know which tool they need. Guides explain signup, billing, credentials, setup and success checks using ordinary Korean and authentic public screenshots.

The website is not an authenticated service manager. There are no API-key inputs. Saved checkmarks are explicitly the visitor's own progress, stored only in the browser. A checked instruction cannot prove that a service is authenticated or that an agent works. Actual provider login, billing approval and runtime checks happen in the user's account/device.

## Design reference

The ui-ux-pro-max design-system search recommended a three-step funnel and readable Korean typography. The implementation adopts those patterns, with warm ivory surfaces, dark green ink, mint/emerald calls to action, restrained borders and SVG icons. Blur-heavy glass effects were rejected because they weaken text contrast and mobile performance.

The beautiful HTML template reference is [Tabler](https://github.com/tabler/tabler), with the [public HTML demo](https://preview.tabler.io/). Its MIT-licensed sidebar, action-card and form organization inform the design. We implement original Next.js components rather than embedding Bootstrap runtime or bundled chart plugins. No Tabler artwork, logos or commercial templates are redistributed.

Accessibility targets: 4.5:1 body text contrast, visible keyboard focus, 44 px controls, persistent explanations for disabled actions, reduced-motion behavior and no horizontal page overflow at 375 px. Compatibility tables may scroll inside labeled containers.

## Action support

| Status | Meaning | Action behavior |
|---|---|---|
| supported | Documented web or platform path | Enabled; does not imply account/runtime validation |
| conditional | Documented path with named dependencies or account requirements | Enabled with prerequisites shown |
| unsupported | This particular action has no supported path on this host | Disabled, reason visible; guide still readable |
| unverified | Evidence is insufficient for this host/path | Local execution disabled; research guidance readable |

The site distinguishes browsing a cloud signup page from installing a local SDK. All four targets can open web guides; Windows cannot perform final iOS builds locally, and Android/iOS do not become desktop Playwright or Unity hosts because a desktop can control them. Python's official mobile embedding documentation does not disprove community Termux or guest routes; those remain separate unverified paths.

Platform detection is browser evidence only, including the iPad desktop-user-agent case. Unknown OS defaults to disabled local actions. Users can manually correct the selection, and the interface labels that selection. It never claims to inspect installed binaries, memory, architecture, credentials or permissions through the browser.

## Browser stack

Default: [Playwright CLI](https://github.com/microsoft/playwright-cli) and its agent skill for Codex; [Playwright](https://playwright.dev/docs/intro) library/test runner for repeatable extraction and regression tests. [Tencent BrowserSkill](https://github.com/Tencent/BrowserSkill) is a separate optional CLI/extension path for the user's existing login browser. There is no documented shared Playwright context or direct backend integration to promise. [agent-browser](https://github.com/vercel-labs/agent-browser) remains a visible alternative.

A bounded Jev advisory selection favored Playwright CLI on the supplied criteria. This did not establish runtime compatibility; official sources and deterministic tests remain the evidence. BrowserSkill's shared login profile is not an isolated security sandbox. Account passwords, MFA and human checkpoints stay with the user.

## Model roles

HY4 Preview and DeepSeek V4.1 Flash are the requested LLM tiers. Seedance 2.5 and Veo 3.1 Lite cover high/normal video. Qwen Image 2.1 Pro/Turbo cover image quality/cost tiers. Jev is a decision service. Separate OpenRouter text, image and video catalogs/API endpoints are preserved; being absent from the ordinary text model list does not prove a media model unavailable. Public metadata is not a successful paid-generation test. Published prices are dated and can change with provider and output settings.
