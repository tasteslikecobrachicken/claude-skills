# Java

Tooling: **Gradle** (Kotlin DSL) by default, Maven if the user or their
organisation wants it. **JUnit 5** for tests, **Spotless** for format,
**Error Prone** or the compiler's own `-Xlint` for static analysis.

Gradle is the default because its init task is non-interactive-friendly,
the Kotlin DSL gives editor completion, and configuration cache makes repeat
builds fast. Maven is the right call when the team already standardises on it —
ask rather than converting them.

## Native init

Gradle's `init` is interactive by default. Pass every option to avoid it
hanging on a prompt:

```bash
gradle init \
  --type java-application \
  --dsl kotlin \
  --test-framework junit-jupiter \
  --package com.example.ferry \
  --project-name ferry \
  --java-version 21 \
  --no-split-project
```

| Project type | `--type` |
| --- | --- |
| Application / CLI | `java-application` |
| Library | `java-library` |
| Gradle plugin | `kotlin-gradle-plugin` |

`--no-split-project` keeps a single module. Drop it for a genuine multi-module
build; don't split a project that has one concern.

Maven equivalent:

```bash
mvn archetype:generate \
  -DgroupId=com.example \
  -DartifactId=ferry \
  -DarchetypeArtifactId=maven-archetype-quickstart \
  -DarchetypeVersion=1.5 \
  -DinteractiveMode=false
```

The quickstart archetype is dated — it still wires up JUnit 4 in some versions.
Check the generated `pom.xml` and replace the test dependency with
`junit-jupiter` if so.

## The wrapper is a hard requirement

`gradle init` generates `gradlew`, `gradlew.bat` and
`gradle/wrapper/gradle-wrapper.jar`. **Everyone runs `./gradlew`, never
`gradle`** — the wrapper pins the build tool version, so the build behaves the
same on every machine and in CI.

`gradle-wrapper.jar` is a binary. You cannot hand-write it. If Gradle isn't
installed, say directly that the scaffold has no wrapper and that
`gradle wrapper` must be run once from a real install. Do not ship a project
whose documented command fails. Maven has the same constraint with
`mvn wrapper:wrapper`.

Commit the wrapper, including the jar. It is the one binary that belongs in a
Java repo.

## build.gradle.kts

What `init` produces is thin. A realistic library build:

```kotlin
plugins {
    `java-library`
    id("com.diffplug.spotless") version "6.25.0"
}

group = "com.example"
version = "0.1.0"

java {
    toolchain {
        languageVersion = JavaLanguageVersion.of(21)
    }
    withSourcesJar()
    withJavadocJar()
}

repositories { mavenCentral() }

dependencies {
    testImplementation(platform("org.junit:junit-bom:5.11.3"))
    testImplementation("org.junit.jupiter:junit-jupiter")
    testRuntimeOnly("org.junit.platform:junit-platform-launcher")
}

tasks.test {
    useJUnitPlatform()
    testLogging { events("passed", "skipped", "failed") }
}

tasks.withType<JavaCompile>().configureEach {
    options.compilerArgs.addAll(listOf("-Xlint:all", "-Werror"))
}

spotless {
    java {
        palantirJavaFormat()
        removeUnusedImports()
    }
}
```

Points worth keeping:

- **`toolchain`**, not `sourceCompatibility`. Gradle then downloads the right
  JDK instead of failing on whatever the machine happens to have.
- **The JUnit BOM** — declare the platform once and omit versions on each
  artifact, so they can never drift apart.
- **`junit-platform-launcher` as `testRuntimeOnly`** is required on current
  Gradle; without it tests fail to start with an unhelpful error.
- **`-Werror`** is a real choice: it stops warning rot, but it will break the
  build on a deprecation in a dependency upgrade. Mention it; drop it if the
  user would rather not.

Check for newer plugin and BOM versions rather than copying those numbers
straight across.

## Layout

Maven's layout, which Gradle also uses:

```
src/main/java/com/example/ferry/App.java
src/main/resources/
src/test/java/com/example/ferry/AppTest.java
src/test/resources/
build.gradle.kts
settings.gradle.kts
gradle/wrapper/
gradlew
.gitignore
```

The package directory chain must match the package declaration exactly. Reverse
domain order, all lowercase, no hyphens or underscores.

## Tests

```java
class ParserTest {
    @Test
    void rejectsEmptyInput() {
        assertThrows(IllegalArgumentException.class, () -> Parser.parse(""));
    }

    @ParameterizedTest
    @ValueSource(strings = {"a=1", "b=2"})
    void acceptsValidPairs(String input) {
        assertNotNull(Parser.parse(input));
    }
}
```

JUnit 5 test classes and methods are package-private — don't write `public`.

## Fallback — no JDK, Gradle or Maven installed

Write `build.gradle.kts`, `settings.gradle.kts`, the source tree, the tests and
`.gitignore` by hand. State plainly that:

1. There is no wrapper, so `./gradlew` will not work yet.
2. The user must install a JDK and Gradle, then run `gradle wrapper` once.
3. Nothing was compiled or tested.

## .gitignore

```gitignore
build/
target/
out/
.gradle/
*.class
*.jar
!gradle/wrapper/gradle-wrapper.jar
.idea/
*.iml
.classpath
.project
.settings/
```

The negation for the wrapper jar matters — a bare `*.jar` rule silently drops
the one jar the project needs.

## Verification loop

```bash
./gradlew build
./gradlew spotlessCheck
./gradlew test
```

`build` already runs `test`; run it separately only to see the output.

## CI (only if requested)

```yaml
name: ci
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-java@v4
        with:
          distribution: temurin
          java-version: '21'
      - uses: gradle/actions/setup-gradle@v4
      - run: ./gradlew build spotlessCheck
```
