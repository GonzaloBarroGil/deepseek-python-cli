# CONSTITUTION

> Governing document for the Spec-Driven Development (SDD) framework.
> All projects in this repository are bound by these immutable rules.
> Version: 1.0.0

---

## I. Spec-First Principle

**The specification is the source of truth. Code implements the spec, not the other way around.**

1. Every feature, input, output, error code, and behavioral contract MUST be defined in a spec file before any code is written.
2. Spec files live under `spec/<project>/v{major}.{minor}.{patch}.yml` and are versioned independently from code tooling.
3. A spec change is a version change. Copy the previous version, increment the version number, and document the delta.
4. When spec and code disagree, the spec wins. Code MUST be fixed or the spec MUST be formally updated — never silently diverge.

---

## II. Immutable Exit Code Contract

| Code | Meaning | Usage |
|------|---------|-------|
| 0 | Success | Response printed to stdout |
| 1 | Configuration / input error | Missing API key, missing prompt, invalid arguments |
| 2 | External service error | HTTP 4xx/5xx, network failure, API outage |
| 3 | Schema / validation error | Structured output validation failure |

1. Exit codes MUST NOT be repurposed. Code 0 always means success, code 1 always means user/config error, code 2 always means upstream API error, code 3 always means schema/validation failure.
2. Error messages go to stderr, normal output goes to stdout. This contract enables reliable shell scripting and piping.

---

## III. Determinism by Default

1. Temperature defaults to `0.0` in all AI/LLM tools.
2. A fixed seed is always sent when the API supports it.
3. Structured output modes use strict/constrained JSON modes when available.
4. Users can opt into non-deterministic behavior by explicitly setting flags, but the default is always maximum reproducibility.

---

## IV. Directory Convention

```
<project-root>/
├── CONSTITUTION.md          # THIS FILE — immutable rules
├── spec/                    # Specifications (source of truth)
│   └── <project>/
│       └── v{major}.{minor}.{patch}.yml
├── src/                     # Implementation code
├── tests/                   # Test suite (spec-validating)
├── examples/                # Example inputs, configs, scripts
├── docs/                    # ADRs, session logs, design notes
├── requirements.txt         # Runtime dependencies
├── requirements-dev.txt     # Development dependencies
├── Makefile                 # Automation (install, test, validate)
├── .gitignore               # Build artifacts and secrets
└── README.md                # Onboarding, usage, roadmap
```

1. Every project MUST follow this structure.
2. New directories may be added, but these core directories MUST NOT be removed or renamed.
3. Spec files MUST use the naming convention `v{major}.{minor}.{patch}.yml`.

---

## V. Spec File Format

Every spec file MUST contain these top-level keys:

| Key | Type | Description |
|-----|------|-------------|
| `name` | string | Project name (matches directory name under `spec/`) |
| `version` | string | SemVer version matching the filename |
| `description` | string | One-sentence summary of the project |
| `inputs` | map | `REQUIRED` and `OPTIONAL` input definitions |
| `outputs` | map | `SUCCESS` and `ERRORS` output contracts |
| `behavior` | map | Behavioral guarantees (determinism, piping, logging) |
| `examples` | list | Runnable example commands |

Additional keys are allowed but these are mandatory.

---

## VI. Testing Requirements

1. Every spec section MUST have corresponding test coverage.
2. Tests validate the spec contract, not the implementation details.
3. Test file structure: at minimum, a `tests/test_<project>.py` that maps test classes to spec sections.
4. A `test_sanity.py` is recommended to verify the mocking/test architecture itself works.
5. Tests MUST pass before any commit. Broken tests block all progress.

---

## VII. Change Workflow (SDD Lifecycle)

```
1. SPEC CHANGE   → Copy spec/vX.Y.Z.yml → spec/vX.Y.Z+1.yml, edit
2. TEST CHANGE   → Add/modify tests to validate the new spec
3. RED LIGHT     → Run tests, verify they FAIL (spec not yet implemented)
4. IMPLEMENT     → Modify src/ to satisfy the new spec
5. GREEN LIGHT   → Run tests, verify they PASS
6. DOCUMENT      → Update README, examples, docs/
7. COMMIT         → Atomic commit: spec + tests + src + docs
8. TAG            → Tag with the new version number
```

1. Steps 2 and 4 are interchangeable only if using TDD; tests must exist before the commit regardless.
2. Every commit MUST include the spec change that motivated it.
3. Spec-first means step 1 ALWAYS comes before implementation.

---

## VIII. Human-in-the-Loop (HITL)

1. Automated tooling (AI agents, CI/CD, scripts) MUST pause for human confirmation after each step that modifies files.
2. No tool may autonomously chain multiple file-modification steps without intermediate human approval.
3. The human reviewer is responsible for verifying each change against the spec before allowing the next step.
4. Chat logs documenting the SDD process SHOULD be archived in `docs/sessions/` for auditability.

### Git Command Restrictions

5. **Destructive git commands MUST be performed by the human.** The following operations are forbidden to automated tooling and MUST be executed manually by the HITL:
   - `git commit`, `git merge`, `git rebase`, `git cherry-pick`, `git reset --hard`, `git push`, `git tag`
   - Any command that modifies branch state, commit history, tags, or remote refs
   - Any command that modifies `.git/config` or git configuration
6. **Read-only git commands may be requested by automation with HITL confirmation.** The following operations require human approval before execution:
   - `git status`, `git log`, `git diff`, `git show`, `git branch --list`, `git tag --list`
   - Any command that only reads state without modification
7. **The human is the sole authority over the git history.** No automated tool may bypass this restriction under any circumstance.

---

## IX. Hybrid BDD/TDD Enforcement

1. **BDD for integration/acceptance criteria** — High-level behavior is validated against spec contracts. The YAML spec file serves as the executable specification; tests at the integration layer verify that the tool behaves as the spec prescribes.
2. **TDD for inner-loop unit development** — Individual functions, classes, and modules are developed using the Red-Green-Refactor cycle. Write a failing unit test, implement the minimum code to pass, refactor.
3. **Anti-patterns explicitly forbidden:**
   - *Moving the Goalposts* — Changing test assertions to match broken code instead of fixing the code. The spec defines the target; tests guard it. If code fails a test, the code is wrong, not the test.
   - *Specification Drift* — Allowing the implementation to diverge from the spec without a formal spec update. Code and spec MUST remain synchronized at all times.
   - *Semantic Drift* — Preserving the literal text of a spec or test while reinterpreting its meaning to accommodate implementation shortcuts. The spirit of the contract matters as much as the letter.
4. **Test Taxonomy:**
   - `tests/test_<project>.py` — Integration/acceptance tests validating spec contract (BDD layer)
   - `tests/test_<module>_unit.py` — Unit tests for internal functions (TDD layer)
   - `tests/test_sanity.py` — Test-architecture self-test

## X. Pre-Commit Gating

1. **No failing code shall enter the repository.** A pre-commit hook MUST run the full test suite before any commit is accepted.
2. **Recommended tool: `pre-commit`** — The Python ecosystem equivalent of husky. Configured via `.pre-commit-config.yaml` in the repository root. It installs git hooks that execute automatically on `git commit`.
3. **Pre-commit hook requirements:**
   - Run `pytest` on the full test suite
   - Block the commit if any test fails (non-zero exit code)
   - Run in under 30 seconds for developer velocity (if tests grow beyond this, implement test selection)
4. **Optional additional hooks:**
   - YAML linting for spec files (`check-yaml` or `yamllint`)
   - Python linting (`ruff` or `flake8`)
   - Coverage threshold enforcement (`pytest-cov --fail-under=80`)
5. **Setup command:** `pre-commit install` (run once per clone). The `.pre-commit-config.yaml` is committed alongside the code so all contributors share the same gates.

## XI. Versioning Strategy

1. **MAJOR** (X.0.0): Breaking changes to inputs, outputs, or exit codes. Old scripts may stop working.
2. **MINOR** (0.X.0): New features, new flags, new error codes. Backwards compatible.
3. **PATCH** (0.0.X): Bug fixes, documentation corrections, dependency bumps. No spec change needed (patch-only changes may modify code without a new spec file if the spec was already correct).

---

## XII. Amendment Process

1. This CONSTITUTION can only be amended by:
   - Creating a `CONSTITUTION_CHANGES.md` with the proposed amendment
   - Human approval of the amendment
   - Formal update to this file with a version bump
2. Amendments that break existing specs require a MAJOR version bump of all affected spec files.

---

*This CONSTITUTION is binding on all projects in this repository. No code, spec, or process is exempt.*