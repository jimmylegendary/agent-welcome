# Next.js + TypeScript + Zustand starter

A minimal App Router project with a feature-oriented layout: a feature owns its service and Zustand state; the page composes the feature. The example is a local counter and makes no network request.

## Run

```sh
npm install
npm run dev
```

Open `http://localhost:3000`. Run `npm run typecheck` before extending the example. Do not put provider keys in browser code or `NEXT_PUBLIC_*` variables; put authenticated API calls behind a server route or trusted backend.

## Structure

```text
src/app/                         route and global layout
src/features/counter/            feature UI, service, and state
```

The versions in `package.json` are starting constraints. Check the official Next.js, React, TypeScript, and Zustand release notes before a production upgrade.
