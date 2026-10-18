---
name: jimmy-web-mobile
description: Use when designing, building, or reviewing a website, web app, or Flutter mobile application.
---

# Jimmy Web and Mobile

Use the repository's framework, component conventions, and package versions unless a change is necessary and explained.

- Clarify the screen's primary user action and make the next step easy to find.
- Keep UI, state, and service boundaries small; use feature folders when they help a user find related code.
- Keep provider keys and privileged API requests on a trusted server. A browser environment variable is public if it is bundled into client code.
- Design loading, empty, error, success, and offline states where the feature needs them. Use semantic controls, keyboard navigation, and readable contrast.
- Keep web, Android, iOS, and desktop support as separate claims. A shared source tree does not prove every build target was tested.
- Run formatting, type checks, and the narrowest relevant test. Report targets you could not build because the device, SDK, signing identity, or service credential is absent.
