# D-012 — confirmed Easy Install expansion (2026-10-17)

This approved expansion supersedes the scope limitation only in D-005/D-008:
Agent Welcome now implements resumable setup routes for the 12 required OS ×
original-agent targets. D-001, D-003, and D-004 remain in force. Code or fixture
coverage must not be represented as runtime support.

D-009 remains the default safety rule with this narrow exception: after the
product displays a concrete plan and the final user gives explicit consent, it
may download and execute the listed official installer via a non-shell argv
adapter. The action records URL, byte count, SHA-256, argv, outcome, and
recovery state. It never requests elevation, weakens security policy, or reruns
an interrupted installer silently. Agent Welcome writes only a state-local
launcher; it does not edit global PATH. This product consent does not authorize
this development run to install agents, authenticate, or perform billable work.

Android is a same-device Termux/PRoot Linux-userland route and iOS a
same-device UTM Linux-guest route. App installation, guest import/boot, MFA,
credentials, and device permissions remain user checkpoints with a completion
probe and resume state. Fixture success cannot set actual-OS, upstream-binary,
authentication, first-task, or `runtime_verified` evidence to true.
