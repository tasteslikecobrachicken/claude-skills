# JavaScript / TypeScript

Tooling: **Prettier** for format, **ESLint** flat config with
`typescript-eslint` for lint, **Vitest** for tests, `tsc` for types. Full
project setup lives in `project-scaffold/references/typescript.md`; this file is
only about style.

## Mechanical — owned by the tools

`prettier.config.mjs` stays nearly empty. The defaults are the entire value
proposition — a team that configures Prettier has reintroduced the argument it
installed Prettier to end.

```js
export default {};
```

Lint rules that carry style weight, in `eslint.config.mjs`:

```js
extends: [js.configs.recommended, tseslint.configs.recommendedTypeChecked],
rules: {
  '@typescript-eslint/no-explicit-any': 'error',
  '@typescript-eslint/no-floating-promises': 'error',
  '@typescript-eslint/consistent-type-imports': 'error',
},
```

`recommendedTypeChecked` needs type information, so it is slower than
`recommended` and worth it — the rules that catch real bugs (floating promises,
unsafe `any` propagation, misused promises in conditionals) are all in the
type-aware set.

In `tsconfig.json`, `"strict": true` is the baseline. Everything in **Types**
below assumes it.

## Judgment rules

### Naming

`camelCase` for values and functions, `PascalCase` for types, classes and
components, `SCREAMING_SNAKE` only for true module-level constants.

No `I` prefix on interfaces and no `T` prefix on types. The compiler knows what
is a type; the prefix is noise carried over from C#.

Type parameters get real names once there is more than one. `<T>` is fine alone;
`<T, U, V>` should be `<Item, Key, Result>`.

### Types

Never `any`. `unknown` at the boundary, then narrow — `any` doesn't silence one
error, it disables checking for everything downstream of that value.

Don't annotate what is inferred. `const n: number = 5` adds nothing and drifts.
Annotate function parameters, public return types, and empty containers
(`const xs: Item[] = []`), and let inference do the rest.

`type` for unions and aliases, `interface` for object shapes that get
implemented or extended. Both work; picking one per purpose stops the coin-flip
in review.

Prefer a union of literals over `enum`:

```ts
type Status = 'idle' | 'loading' | 'done';        // yes
enum Status { Idle, Loading, Done }               // no
```

Enums emit runtime code, don't narrow as cleanly, and `const enum` breaks under
isolated modules. The union is checked at compile time and erases to nothing.

`as` is an assertion that the compiler is wrong. It usually isn't. Same for `!`
— if a value can be null, handle it; if it genuinely can't, fix the type.

`??` for defaults, not `||`. `||` treats `0` and `''` as absent, which is a bug
that surfaces months later on the one input that happens to be zero.

### Errors

Throw `Error` or a subclass, never a string or an object literal — anything else
loses the stack trace.

Every promise is awaited, returned, or explicitly `void`-ed. A floating promise
means rejections vanish and ordering is undefined; the lint rule above catches
it, so leave it on.

`catch` binds `unknown`, not `Error`. Narrow before using it:

```ts
catch (err) {
  if (err instanceof HttpError) { ... }
  throw err;
}
```

Don't catch merely to re-throw the same error. Either add context or let it
propagate.

### Structure

Named exports, not default. Default exports get renamed freely at each import
site, which defeats grep and makes refactoring tools less useful.

Barrel files (`index.ts` re-exporting a directory) are fine at a package
boundary and a liability inside one, where they create import cycles and drag
the whole module graph into every test. Don't add one per folder by reflex.

Keep modules focused. A file that needs a table of contents in comments is two
files.

Discriminated unions over optional-field soup:

```ts
type Result =
  | { ok: true; value: Data }
  | { ok: false; error: Error };
```

The compiler then guarantees you checked, which `{ value?: Data; error?: Error }`
never can.

### Documentation

TSDoc on exported API. Skip it where the signature says everything — a comment
restating `function getUser(id: string): User` is pure cost.

Document the non-obvious: units, ranges, what throws, whether something mutates
its argument, and why a surprising line exists.

### Idioms

`const` by default, `let` when reassigned, `var` never.

`async`/`await` over `.then()` chains. Mixing both in one function is how
ordering bugs get in.

`for...of` over `forEach` when the body is async or needs `break` — `forEach`
silently ignores both.

Optional chaining and nullish coalescing over manual guard ladders, but not to
paper over a value that shouldn't be null in the first place.

## Commands

```bash
npx prettier --write .        # autofixing
npx eslint --fix .            # autofixing
npx eslint .                  # report only
npx tsc --noEmit              # report only
npx vitest run                # report only
```

## Sweep notes

Prettier on a codebase that used semicolon-free style, or a different line
width, rewrites essentially every line. Land it as one commit and add it to
`.git-blame-ignore-revs` — a whole-repo reformat that destroys `git blame` is
avoidable and people will be annoyed about it for years.

`eslint --fix` can change behaviour. `no-unused-vars` removals are usually safe;
fixes touching promises, `prefer-const` on captured variables, or anything in a
plugin's autofix set are not guaranteed to be. Run the suite after the autofix
commit specifically.

Turning on `strict` in an existing project is not a sweep step. It is a project
in itself — do it per-file with `// @ts-expect-error` budgets, or per-directory
via a second `tsconfig`, and never by leaving the build red.

If the repo has no type-aware linting yet, enabling `recommendedTypeChecked`
will surface a large backlog at once. Report the count before enabling it.
