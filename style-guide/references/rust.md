# Rust

Tooling: all first-party. **rustfmt** for format, **clippy** for lint,
`cargo test` for tests. There is nothing to choose. Full project setup lives in
`project-scaffold/references/rust.md`; this file is only about style.

## Mechanical — owned by the tools

`rustfmt.toml` stays near-empty — the default style is the community standard
and most interesting options are still nightly-only:

```toml
edition = "2021"
```

Lints in `Cargo.toml`:

```toml
[lints.rust]
unsafe_code = "forbid"
missing_debug_implementations = "warn"

[lints.clippy]
all = { level = "warn", priority = -1 }
pedantic = { level = "warn", priority = -1 }
```

`priority = -1` on the groups is required — lint groups must rank below
individual lints or cargo rejects the manifest as soon as you override one rule
out of a group.

`pedantic` fires on reasonable code. Keep it at `warn`, never `deny`.

## Judgment rules

### Naming

`snake_case` for functions, variables and modules; `PascalCase` for types and
traits; `SCREAMING_SNAKE` for constants and statics. Clippy enforces most of
this, so the judgment part is what's left:

Conversion methods follow the convention that tells callers the cost:
`as_` is a cheap borrow, `to_` allocates, `into_` consumes. Getting these
backwards is actively misleading.

`new` returns `Self` without arguments beyond the essential. Anything with many
options gets a builder rather than `new_with_everything`.

### Types

Borrow in parameters, own in returns. `&str` not `&String`, `&[T]` not
`&Vec<T>` — a `&String` parameter rejects string literals for no benefit.

Clone deliberately. `.clone()` sprinkled to escape the borrow checker is a
design that hasn't been worked out yet; `.clone()` because you genuinely need a
second owned copy is fine. The difference is whether you can say which.

Newtypes for domain values. `struct UserId(u64)` costs nothing at runtime and
makes it impossible to pass an order ID where a user ID belongs.

Derive generously: `Debug` on everything, `Clone`, `PartialEq`, `Eq`, `Hash`
where meaningful, `Default` where a zero value makes sense.

`impl Trait` in argument position for simple generic parameters; a named
parameter with a `where` clause once there are bounds worth reading.

Reach for `Rc<RefCell<T>>` last. It moves borrow checking to runtime, where the
failure is a panic instead of a compile error. It is right for genuine shared
mutable graphs and wrong as a way to stop fighting the compiler.

### Errors

Libraries define their own error type — `thiserror` for the boilerplate.
Binaries use `anyhow`. Never `anyhow` in a library: it erases the type, so
callers can't match on what went wrong.

```rust
#[derive(Debug, thiserror::Error)]
pub enum ConfigError {
    #[error("read {path}")]
    Read { path: PathBuf, #[source] source: io::Error },
}
```

`?` for propagation. A `match` on a `Result` that only re-wraps is `?` with
extra steps.

No `unwrap` or `expect` in library code. In `main`, in tests, and after a check
the compiler can't see, they're fine — and there `expect` with a message saying
*why it can't fail* beats `unwrap` every time.

`panic!` is for broken invariants, not for bad input. Anything a caller could
trigger returns `Result`.

### Structure

Small modules with explicit `pub`. Default to private and widen deliberately —
`pub(crate)` covers most of what feels like it needs `pub`.

Iterator chains over index loops. `for (i, x) in xs.iter().enumerate()` when you
need the index; indexing by hand invites the off-by-one and the panic.

Exhaustive `match` over `if let` chains when handling an enum — the compiler
then tells you about the variant you added. A catch-all `_ =>` arm on your own
enum gives that up.

Lifetimes in a struct mean the struct borrows. That is sometimes right and often
a sign an owned type would be simpler. Don't add a lifetime parameter to avoid
one allocation on a cold path.

### Documentation

`///` on public items, `//!` at the top of the crate and each module. Document
what the type system can't state: panics, errors, safety requirements,
complexity.

Doc examples are compiled and run by `cargo test`, so they cannot rot. That
makes them the highest-value documentation in the language — prefer one over
three paragraphs of prose.

`# Panics`, `# Errors` and `# Safety` sections where they apply. `# Safety` on
every `unsafe fn` is not optional.

### Idioms

`Option` combinators (`map`, `and_then`, `unwrap_or_else`) over `match` when the
chain stays readable; `match` once it doesn't.

`?` on `Option` inside a function returning `Option` — it works there too.

Implement `From` rather than a bespoke `to_other()`, and `Display` rather than a
`to_string()` method. Both get you conversions the ecosystem already knows how
to call.

Prefer `&self` methods. Take `self` only when the type is genuinely consumed,
like a builder's `build`.

## Commands

```bash
cargo fmt                              # autofixing
cargo clippy --fix --allow-dirty       # autofixing
cargo fmt --check                      # report only
cargo clippy --all-targets -- -D warnings   # report only
cargo test                             # report only
```

`--all-targets` makes clippy lint tests and benches too, which is exactly where
lint debt accumulates.

## Sweep notes

`cargo fmt` is behaviour-preserving and usually a small diff, since most Rust
repos are already formatted. One commit if it isn't.

`cargo clippy --fix` rewrites source. It requires a clean tree by default —
`--allow-dirty` overrides that, which is precisely why the sweep insists on
committing first rather than passing the flag. Most clippy fixes are
semantically identical, but `needless_borrow`, `redundant_clone` and the
iterator suggestions do change what runs. Test after the fix commit.

`pedantic` on an unlinted codebase produces hundreds of warnings, many of which
are style preferences the project may reasonably reject. Report the count, agree
which lints to keep, and `allow` the rest at crate level with a comment — don't
grind through fixes nobody asked for.

`unsafe_code = "forbid"` will fail to compile a crate that legitimately uses
`unsafe`. Check for `unsafe` blocks before adding that line.
