---
trigger: always_on
---

# Python Environment Management Rules

## 1. Detection

- **Check for Virtual Environment**: Always check for a `.venv` or `venv` directory at the project root before running any command.

## 2. Execution

- **No Global Commands**: Do not use global `python`, `pip`, or `pytest` commands.
- **Use Virtual Environment Paths**:
  - **Python**: Use `.\.venv\Scripts\python.exe` (Windows) or `./.venv/bin/python` (Unix).
  - **Pip**: Use `.\.venv\Scripts\python.exe -m pip` or `.\.venv\Scripts\pip.exe`.
  - **Pytest**: Use `.\.venv\Scripts\pytest.exe` or `.\.venv\Scripts\python.exe -m pytest`.
  - **Other Tools**: Locate tools (ruff, mypy, etc.) within `.venv\Scripts\` or `.venv/bin/`.
- **Dependency Management**: Use `pyproject.toml` for managing project dependencies under the `[project.dependencies]` section rather than `requirements.txt`.
- **Linting**: Always lint and format with Ruff before presenting work. Run `ruff check .` and `ruff format .`.
- **Version Control**: Never automatically commit to Git for the user unless explicitly told.

## 3. Environment Constraint

- **Strict Virtual Environment Usage:** All Python execution, package management, and testing MUST occur within the project's virtual environment (`.venv`).
- **No Global Python:** Never use the system-level Python or global binaries. Never update system-level Python. Never modify system-level Python packages.

## 4. Project Structure Execution

- **CLI Tool:** The project utilizes a modern `src/` structure setup via `pyproject.toml`. To launch the main tool locally, use the generated executable `image-converter` or `python -m image_converter` rather than directly calling `python main.py`.

## 5. Agent Knowledge

### Reading Learnings
Before starting any task, read `.agent/learning/python.md` (create if missing). This file contains accumulated learnings specific to Python work in this codebase. Apply any relevant entries to inform your approach before writing a single line of code.

### Recording Learnings
Your learning file is **NOT a work log** — do not record routine progress or successful changes without surprises. Only add an entry when you discover something that would meaningfully change how you or another agent approaches this codebase in the future.

**✅ ONLY add entries when you discover:**
- A virtualenv, packaging, or `pyproject.toml` behavior that was unexpectedly required by this codebase's setup
- A Ruff, mypy, or pytest behavior that behaved differently than expected in this project's configuration
- A refactor or change that was rejected, and the reason why
- A codebase-specific Python pattern or anti-pattern (e.g. how errors are raised, how modules are structured)
- A surprising edge case in how this project handles imports, dependencies, or the `src/` layout

**❌ DO NOT record:**
- "Implemented feature X" (unless there's a non-obvious learning)
- Generic Python tips that apply to any project
- Successful changes that went exactly as expected

**Format:**
```
## YYYY-MM-DD - [Title]
**Learning:** [What you discovered and why it matters]
**Action:** [How to apply this next time]
```

### File Layout
Learnings are separated by language, one file per language, all under `.agent/learning/`:
- Python → `.agent/learning/python.md`
- Rust → `.agent/learning/rust.md`
- TypeScript/JavaScript → `.agent/learning/typescript.md`
- (Add new files for other languages as needed)

## 6. General Development Rules

- **Documentation Updates**: Every change should update the documentation (MkDocs) and the `README.md` appropriately.
- **Docstrings**: Every change should update docstrings for all modified or new functions.
- **Testing**: Testing should be added for all new functions. Add new functions and options to `automated_testing.py`.

---

# Lore Protocol -- Agent Instructions

## What Is Lore

Lore embeds structured decision context (constraints, rejected alternatives, directives) into git commit trailers. It is queryable via the `lore` CLI. Protocol version: 1.0.

## Before Modifying Any File

Run these commands for every file or directory you are about to change:

```sh
lore constraints <path> --json
lore rejected <path> --json
lore directives <path> --json
```

- **Constraint** = hard requirement. Do not violate.
- **Rejected** = approach tried and abandoned (`alternative | reason`). Do not re-explore.
- **Directive** = standing instruction. Follow it.

If constraints exist, verify your changes comply. If a rejected alternative matches your plan, choose differently.

## When Committing

Stage changes with `git add`, then pipe JSON to `lore commit`:

```sh
echo '{
  "intent": "fix: handle null user in auth middleware",
  "body": "Previously threw 500 on null user. Now returns 401.",
  "trailers": {
    "Constraint": ["must not throw -- return 401 instead"],
    "Rejected": ["silent redirect to login | breaks API clients"],
    "Confidence": "high",
    "Scope-risk": "narrow",
    "Tested": ["null user returns 401", "valid user still works"],
    "Not-tested": ["concurrent request race condition"]
  }
}' | lore commit
```

### JSON Schema

```json
{
  "intent": "string (REQUIRED) -- max 72 chars",
  "body": "string (optional)",
  "trailers": {
    "Constraint": ["string array"],
    "Rejected": ["format: 'alternative | reason'"],
    "Confidence": "'low' | 'medium' | 'high'",
    "Scope-risk": "'narrow' | 'moderate' | 'wide'",
    "Reversibility": "'clean' | 'migration-needed' | 'irreversible'",
    "Directive": ["string array"],
    "Tested": ["string array"],
    "Not-tested": ["string array"],
    "Supersedes": ["8-char hex Lore-id"],
    "Depends-on": ["8-char hex Lore-id"],
    "Related": ["8-char hex Lore-id"]
  }
}
```

Only `intent` is required. `Lore-id` is auto-generated.

### When to Add Trailers

| Situation | Trailer |
|-----------|---------|
| Chose A over B | `Rejected: ["B \| reason"]` |
| Rule must hold | `Constraint: ["the rule"]` |
| Future instruction | `Directive: ["the instruction"]` |
| Unsure | `Confidence: "low"` |
| Hard to undo | `Reversibility: "migration-needed"` |
| Known gap | `Not-tested: ["the gap"]` |

## Other Commands

| Command | Purpose |
|---------|---------|
| `lore context <path> --json` | Full context for a file/directory |
| `lore why <file>:<line> --json` | Line-level blame with Lore context |
| `lore search --text "q" --json` | Search across all lore |
| `lore stale <path> --json` | Check for outdated decisions |
| `lore trace <lore-id> --json` | Trace a decision chain |