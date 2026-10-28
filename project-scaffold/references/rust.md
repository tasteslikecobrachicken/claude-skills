# Rust

Tooling: all first-party. **cargo** for build and dependencies, **rustfmt**
for format, **clippy** for lint, `cargo test` for tests. There is no decision
to make here — use them.

## Native init

| Project type | Command |
| --- | --- |
| Library | `cargo new --lib <name>` |
| Binary / CLI | `cargo new <name>` (`--bin` is the default) |
| In an existing directory | `cargo init` |
| Workspace | Create the root `Cargo.toml` by hand, then `cargo new` each member |

`cargo new` runs `git init` unless the directory is already a repo, and writes
a `.gitignore`. Check before adding your own.

The crate name and the binary name are separate: a crate named `ferry-cli` can
produce a binary named `ferry` via a `[[bin]]` section.

## Cargo.toml

Configure lints in the manifest with the `[lints]` table rather than
`#![deny(...)]` at the crate root or flags in CI — manifest lints apply to every
invocation, including the user's editor:

```toml
[package]
name = "<name>"
version = "0.1.0"
edition = "2021"
rust-version = "1.82"

[dependencies]

[lints.rust]
unsafe_code = "forbid"          # drop this if the crate genuinely needs unsafe
missing_debug_implementations = "warn"

[lints.clippy]
all = { level = "warn", priority = -1 }
pedantic = { level = "warn", priority = -1 }
```

The `priority = -1` is required: lint *groups* must have lower priority than
individual lints, or cargo rejects the manifest when you later override a
single rule out of the group.

`pedantic` is opinionated and will fire on reasonable code. Keep it at `warn`,
never `deny`, and tell the user they can drop that line.

Set `edition` to the current stable edition, and `rust-version` to the oldest
release you'll support — it turns a confusing compile error into a clear one for
anyone on an older toolchain.

## Layout

```
src/lib.rs               # library crate root
src/main.rs              # binary crate root
src/<module>.rs
tests/<name>.rs          # integration tests — see the crate as an external user
benches/                 # only if there's something to benchmark
Cargo.toml
rustfmt.toml
```

A crate can have both `lib.rs` and `main.rs`: put the logic in the library and
keep `main.rs` to argument parsing and a call into it. That makes the logic
testable from `tests/`, which cannot see a binary-only crate.

## Tests

Unit tests live in the file they test, in a `#[cfg(test)]` module — this is
idiomatic in Rust, not a smell, and it's the only way to test private items:

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parses_empty_input() {
        assert!(parse("").is_err());
    }
}
```

Integration tests in `tests/` can only reach the public API. Having one of each
from the start proves both paths work.

## rustfmt.toml

Keep it empty or near-empty. The default style is the community standard and
most useful options are still nightly-only:

```toml
edition = "2021"
```

## Fallback — no Rust installed

Every file above is plain text; write them all. Never hand-write `Cargo.lock`.

Tell the user to install via `rustup` (the official installer — distro packages
lag badly and often lack `clippy`/`rustfmt`), then run `cargo build`. Print the
command; don't run it.

## .gitignore

```gitignore
/target
**/*.rs.bk
*.pdb
```

For a **library**, also ignore `Cargo.lock` — libraries should build against
their dependents' resolved versions. For a **binary**, commit it, so builds are
reproducible. This is the one `.gitignore` decision that depends on project
type, so get the type right before writing the file.

## Verification loop

```bash
cargo build
cargo fmt --check
cargo clippy --all-targets -- -D warnings
cargo test
```

`--all-targets` makes clippy lint tests and benches too, which is where lint
debt otherwise accumulates.

## CI (only if requested)

```yaml
name: ci
on: [push, pull_request]
env:
  CARGO_TERM_COLOR: always
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: dtolnay/rust-toolchain@stable
        with:
          components: rustfmt, clippy
      - uses: Swatinem/rust-cache@v2
      - run: cargo fmt --check
      - run: cargo clippy --all-targets -- -D warnings
      - run: cargo test
```

`Swatinem/rust-cache` is worth the extra action — Rust CI without a cache is
slow enough that people start skipping it.
