# Java

Tooling: **Spotless** with `palantirJavaFormat` for format, the compiler's own
`-Xlint:all` for lint, **JUnit 5** for tests. Full project setup lives in
`project-scaffold/references/java.md`; this file is only about style.

## Mechanical — owned by the tools

```kotlin
spotless {
    java {
        palantirJavaFormat()
        removeUnusedImports()
    }
}

tasks.withType<JavaCompile>().configureEach {
    options.compilerArgs.addAll(listOf("-Xlint:all", "-Werror"))
}
```

Palantir's format is Google's with wider lines and less aggressive wrapping. It
has no options, which is the point — brace position, import order, wrapping and
indentation stop being discussable.

`-Werror` turns warning rot into a build failure. It is a real trade: a
deprecation in a dependency upgrade will break the build. Keep it unless the
user objects.

Checkstyle and PMD are not in the default stack. Adding them means owning a
rule-set, and most of what they catch is either handled above or is judgment
that belongs below.

## Judgment rules

### Naming

Standard conventions are enforced socially, not by tooling, so they still
belong here: `PascalCase` types, `camelCase` members, `SCREAMING_SNAKE`
constants, lowercase package names with no underscores.

No `Impl` suffix. `UserServiceImpl` as the only implementation of
`UserService` means the interface exists for no reason — delete the interface
and keep the class, or name the implementation for how it differs
(`PostgresUserRepository`, `CachingRateLimiter`).

Don't abbreviate. `Configuration` not `Cfg`, `message` not `msg`. Verbosity is
the language's existing tax; abbreviating pays it twice.

### Types

`record` for anything that is data. It gives you the constructor, accessors,
`equals`, `hashCode` and `toString`, all correct, and it states immutability in
one word.

Fields `final` unless there is a reason. Mutability is a design decision worth
defending, not a default.

Program to interfaces in signatures — `List<T>` as a parameter type, not
`ArrayList<T>` — but return the concrete guarantee your callers need.

`var` where the right side names the type (`var users = new ArrayList<User>()`),
not where it hides it (`var result = process(x)`).

### Errors

Never `catch (Exception e)` at a point that can't handle everything. Catch the
specific types; let the rest reach the boundary that logs and fails.

`e.printStackTrace()` is not error handling. It writes to stderr, ignores the
logging config, and loses the event in production. Log through the logger with
the exception as the last argument.

Never swallow. An empty catch block, or one that logs at `debug` and continues,
converts a fault into corrupted state:

```java
catch (IOException e) { }                          // no
catch (IOException e) { throw new LoadFailed(path, e); }   // yes
```

Wrapping must preserve the cause. A new exception without the original loses
the only stack trace that said what happened.

`Optional` is a return type. Not a field, not a parameter, not a collection
element — it is serialization-hostile and an `Optional` parameter just means two
methods that weren't written.

Return empty collections, never `null`. `Collections.emptyList()` costs nothing
and removes an entire class of caller-side check.

### Structure

Constructor injection, with `final` fields. Field injection hides dependencies
from the constructor, which is the one place a reader looks for them, and makes
the class untestable without a framework.

Static mutable state is shared global state. It breaks test isolation and
concurrency simultaneously. Static `final` immutable constants are fine.

Keep methods short enough to see whole. A method needing section comments is
several methods.

Package by feature, not by layer. `order/` containing its controller, service
and repository beats `controllers/`, `services/`, `repositories/` each
containing a slice of everything — features get added and deleted as units.

### Documentation

Javadoc on public API. Document what the caller can't see: nullability,
thread-safety, what it throws and when, whether it mutates its arguments,
performance characteristics that would surprise.

Skip Javadoc that restates the signature. `/** Gets the name. */` on
`getName()` is noise that has to be maintained.

### Idioms

Streams where they clarify — a map-filter-collect pipeline reads well. A stream
with side effects in `forEach`, or nested `flatMap`s over three collections, is
a loop that got ashamed of itself.

`equals`/`hashCode` always together, or neither, or use a `record`.

Try-with-resources for anything `Closeable`. A manual `finally { close(); }` is
either wrong about suppressed exceptions or reimplementing the language.

## Commands

```bash
./gradlew spotlessApply       # autofixing
./gradlew spotlessCheck       # report only
./gradlew compileJava         # report only (-Werror makes warnings fail)
./gradlew test                # report only
```

## Sweep notes

`spotlessApply` on a codebase formatted by hand, or by a different formatter,
rewrites nearly every file. One commit, then `.git-blame-ignore-revs`.

`removeUnusedImports()` is the one part of Spotless that can change behaviour.
Java has no import side effects, so this is usually safe — but a removed import
of a class referenced only in Javadoc `@link` will break the Javadoc build, and
annotation processors occasionally key off imports. Build after the format
commit, don't just format.

Turning on `-Werror` in an existing project will fail the build on accumulated
deprecation warnings. Count them first and report the number; enabling it is a
separate decision from formatting.

Converting classes to `record`s is a judgment commit, not a mechanical one. It
changes the generated `equals`/`hashCode` and can break anything relying on
identity semantics or on subclassing. One class at a time, tests after each.
