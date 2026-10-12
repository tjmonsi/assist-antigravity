---
name: run-test
description: >-
  Internal: preloaded by the qa agent. Run existing test suites (unit and integration), capture coverage metrics,
  and produce consolidated test reports. Used by QA to validate implementations.
metadata:
  effort: "high"
  user-invocable: "false"
---

# Run Test

Execute existing test suites, capture coverage, and produce consolidated test reports.

## Contents

1. [Language Detection](#language-detection)
2. [Test Execution](#test-execution)
3. [Coverage Capture](#coverage-capture)
4. [Report Format](#report-format)
5. [Best Practices](#best-practices)

---

## Language Detection

Detect the project language from the codebase and run appropriate test commands:

| Signal | Test Command | Coverage Command |
|--------|--------------|------------------|
| Python (`pytest`, `pyproject.toml`) | uv: `uv run --no-sync --no-python-downloads pytest tests/`<br>else: `pytest tests/` | uv: `uv run --no-sync --no-python-downloads pytest --cov=src --cov-report=term-missing`<br>else: `pytest --cov=src --cov-report=term-missing` |
| TypeScript/Node (`vitest`, `package.json`) | `npm run test` or `npx --no vitest run` | `npx --no vitest run --coverage` |
| JavaScript (`jest`, `package.json`) | `npm test` or `npx --no jest` | `npx --no jest --coverage` |
| Go (`go.mod`) | `go test -v ./...` | `go test -cover ./...` |
| Rust (`Cargo.toml`) | `cargo test --lib` | `cargo tarpaulin --out Html` |
| Kotlin (`build.gradle.kts`) | `./gradlew test` | `./gradlew testDebugUnitTest jacocoTestDebugUnitTestReport` |

## Test Execution

### Run all tests

Execute the full test suite (unit + integration):

```bash
# Python (uv first; needs an existing .venv, create it with `uv sync`)
uv run --no-sync --no-python-downloads pytest tests/
# Python without uv (activated virtual environment)
pytest tests/

# TypeScript/JavaScript
npm test

# Go
go test ./...

# Rust
cargo test

# Kotlin
./gradlew test
```

**Python and uv:** detect uv with `command -v uv` (also `uv.lock` or `[tool.uv]` in `pyproject.toml`). With uv, run tests as `uv run --no-sync --no-python-downloads pytest ...`: it neither installs packages nor downloads Python, but it needs an existing `.venv`. Before running it, use `find_by_name` to look for `.venv/bin/pytest` (`.venv/Scripts/pytest.exe` on Windows); if missing, show the user `uv sync` and stop. Plain `uv run` syncs the environment first, so agents do not use it. If a test dependency is missing, show the user `uv add --dev pytest pytest-cov` then `uv sync`; without uv, show `python -m pip install pytest pytest-cov` for the project's virtual environment. Agents never run these.

**Node runners:** call a locally installed runner through `npx --no` (`npx --no vitest run`, `npx --no jest`). The `--no` flag makes npx fail instead of downloading a missing package; if it fails, show the user the install command and stop.

### Capture test results

For each language, capture:
1. **Test pass/fail counts** — how many tests passed, failed, skipped
2. **Execution time** — total time to run suite
3. **Error messages** — detailed failure output for failed tests
4. **Test names** — which specific tests failed

### Document test environment

Record:
- Language version (Node 18.x, Python 3.11, Go 1.21, etc.)
- Framework versions (pytest, vitest, jest, etc.)
- Test runner configuration (timeout settings, parallelization)

---

## Coverage Capture

### Run coverage tool per language

Use the commands in [references/coverage-commands.md](references/coverage-commands.md).

### Parse coverage output

Extract:
- **Line coverage %** — percentage of code lines executed
- **Branch coverage %** — conditional paths exercised
- **Uncovered files** — which files have gaps
- **Uncovered lines** — specific line numbers not tested

### Assess against target

Target: **90% code coverage minimum**

If below 90%:
1. List uncovered files and lines
2. Identify high-risk uncovered paths (error handlers, auth flows)
3. Report as a finding requiring remediation

---

## Report Format

Use the template in [references/test-report-template.md](references/test-report-template.md).

The report structure:
- **What was tested:** Test suite name, language, framework
- **Pass/fail counts:** Number of passed, failed, skipped tests
- **Coverage vs. target:** Actual % vs. 90% minimum
- **For every failure:** Test name, how it was invoked, captured output/logs
- **Recommendations:** Tests to add, failures to fix, coverage gaps to address

Apply the Report Writing Standard:
- Lead with the most important finding (coverage gap, blocking failure)
- No meta-headers ("What follows", "Key takeaway")
- No severity badges or emoji
- Three-part finding: what happened, why it matters, what to do next
- One optional summary line only at the very end

---

## Best Practices

1. **Run full suite:** Execute all unit + integration tests together, not selectively.
2. **Capture all output:** Log full error messages, stack traces, and failure details.
3. **Record environment:** Note Node version, Python version, etc., for reproducibility.
4. **No flaky test ignoring:** If tests flake, investigate and fix — don't skip.
5. **Parallel execution:** If the test suite supports parallel workers, use 4-8 workers to speed execution.
6. **Timeout handling:** If tests timeout, investigate whether the timeout is too short or the test is genuinely slow.
7. **Coverage files:** Save coverage reports for manual inspection (HTML, JSON) in `coverage/` directory.
8. **Installs belong to the user:** If a coverage tool is missing, show the install command from the coverage reference and wait. Never run `pip install`, `npm install`, `cargo install`, or `npx` downloads yourself.

---

## Workflow

1. **Detect language** from the codebase (go.mod, package.json, Cargo.toml, etc.)
2. **Read the test configuration** (pytest.ini, jest.config.js, Cargo.toml, etc.)
3. **Run test suite** using language-appropriate command
4. **Capture results:** Pass/fail counts, execution time, error messages
5. **Run coverage tool** using language-appropriate command
6. **Parse coverage:** Extract %, identify uncovered files/lines
7. **Generate report** using test-report-template.md
8. **Present to user** — report states verdict (PASS/FAIL/NEEDS ATTENTION) and next steps

---

## Common Issues and Solutions

### Tests timeout
- **Check:** Is the timeout setting in configuration correct for the environment?
- **Solution:** Increase timeout if legitimate (slow I/O, real database), or investigate why tests are slow.

### Flaky tests (pass sometimes, fail sometimes)
- **Symptom:** Same test fails on second run but passed on first
- **Solution:** Investigate for race conditions, non-deterministic behavior, shared state. Do not skip flaky tests.

### Coverage gaps in high-risk areas
- **Symptom:** Error handlers, auth middleware, boundary conditions have <50% coverage
- **Solution:** Report as HIGH priority. Add tests for those paths before release.

### Tests don't run at all
- **Check:** Are test dependencies installed? Is the test framework configured?
- **Solution:** Verify test setup, list missing dependencies and show the user the install command (never install them yourself), check configuration files.
