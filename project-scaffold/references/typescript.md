# JavaScript / TypeScript

Default to TypeScript even when the user says "JavaScript", but say that you
did and offer plain JS. If they want JS, keep everything below and drop the
`tsconfig.json` and the `typescript-eslint` layer — `@eslint/js` and Vitest work
unchanged.

Tooling: **ESLint** (flat config) for lint, **Prettier** for format, **Vitest**
for tests, **tsc** for type checking. Pick one package manager from whatever is
installed and use it consistently; don't mix lockfiles.

## Native init

| Project type | Command |
| --- | --- |
| Web app | `npm create vite@latest <name>` — pass `-- --template react-ts` etc. to skip the prompts |
| Library / CLI / server | `npm init -y`, then add TypeScript by hand — the generators here are framework-specific and pull in more than a library needs |

Vite's templates are current and already wire up TS and a dev server. They do
**not** set up ESLint, Prettier or a test runner.

```bash
npm i -D typescript @types/node eslint @eslint/js typescript-eslint \
         prettier vitest
```

`typescript-eslint` is the single modern package. If you see
`@typescript-eslint/parser` and `@typescript-eslint/eslint-plugin` installed
separately, that's the pre-v7 layout — replace them.

## Config

**`eslint.config.mjs`** — flat config. `.eslintrc*` is dead; don't write one.

```js
import js from '@eslint/js';
import { defineConfig } from 'eslint/config';
import tseslint from 'typescript-eslint';

export default defineConfig({
  files: ['**/*.{js,ts}'],
  extends: [js.configs.recommended, tseslint.configs.recommendedTypeChecked],
  languageOptions: {
    parserOptions: {
      projectService: true,
      tsconfigRootDir: import.meta.dirname,
    },
  },
});
```

`recommendedTypeChecked` needs type information and so is slower than
`recommended`, but it catches the errors worth catching — floating promises,
unsafe `any` flow. Use `projectService: true`, not the older `project: true`.

**`tsconfig.json`** — the `moduleResolution` value depends on who consumes the
output:

```jsonc
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2022"],
    "module": "nodenext",
    "moduleResolution": "nodenext", // "bundler" if Vite/webpack consumes it
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitOverride": true,
    "verbatimModuleSyntax": true,
    "declaration": true,
    "sourceMap": true,
    "outDir": "dist",
    "rootDir": "src",
    "skipLibCheck": true
  },
  "include": ["src"]
}
```

`strict` alone is not strict enough: `noUncheckedIndexedAccess` is the one that
catches the common `arr[i]` crash, and it is not in `strict`.

**`package.json`** — set `"type": "module"` and real scripts:

```jsonc
{
  "type": "module",
  "scripts": {
    "build": "tsc",
    "typecheck": "tsc --noEmit",
    "lint": "eslint .",
    "format": "prettier --write .",
    "format:check": "prettier --check .",
    "test": "vitest run"
  }
}
```

A published library also needs `"exports"`, `"files"`, and `"types"`. A CLI
needs `"bin"`.

**`prettier.config.mjs`** — keep it nearly empty; the defaults are the point.

```js
export default { singleQuote: true };
```

## Layout

```
src/index.ts
src/<module>.ts
src/<module>.test.ts     # colocated, or tests/ — pick one
tsconfig.json
eslint.config.mjs
prettier.config.mjs
package.json
.gitignore
```

Vitest finds `*.test.ts` anywhere by default, so no config file is needed until
you want coverage thresholds or a jsdom environment.

## Fallback — no Node installed

Write every file above by hand; they're all plain text. Leave
`node_modules/` and the lockfile absent and tell the user to run
`npm install`. Never hand-write `package-lock.json`.

## .gitignore

```gitignore
node_modules/
dist/
build/
coverage/
*.tsbuildinfo
.env
.env.local
.DS_Store
npm-debug.log*
```

## Verification loop

```bash
npm install
npm run lint
npm run format:check
npm run typecheck
npm test
```

## CI (only if requested)

```yaml
name: ci
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: lts/*
          cache: npm
      - run: npm ci
      - run: npm run lint
      - run: npm run format:check
      - run: npm run typecheck
      - run: npm test
```

`npm ci` requires a committed lockfile. If the scaffold was hand-written and no
lockfile exists yet, use `npm install` until the first real install lands.
