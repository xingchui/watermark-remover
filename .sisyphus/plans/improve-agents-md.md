# Work Plan: Improve AGENTS.md for watermark_remover

## TL;DR

> **Quick Summary**: Analyze the watermark_remover codebase and improve the existing AGENTS.md file with accurate build/test commands, code style guidelines, module structure, and testing patterns based on actual codebase analysis.
> 
> **Deliverables**: 
> - Updated `AGENTS.md` at project root (~150 lines)
> 
> **Estimated Effort**: Quick
> **Parallel Execution**: NO - single file update
> **Critical Path**: Research → Write AGENTS.md

---

## Context

### Original Request
User requested analysis of the codebase to create/improve an AGENTS.md file containing:
1. Build/lint/test commands - especially for running a single test
2. Code style guidelines including imports, formatting, types, naming conventions, error handling, etc.

### Interview Summary
**Key Findings from Codebase Analysis**:
- Project uses **pytest** for testing
- Tests located in `tests/` directory
- Single test command: `pytest tests/test_file.py::test_name -q`
- Code uses Python 3.8+ with type annotations
- Google-style docstrings used throughout
- Custom exception hierarchy (`WatermarkRemoverError` base class)
- Dataclasses for structured data
- No Cursor/Copilot rules found in repository
- No pre-commit hooks configured

**Research Findings**:
- Project structure: `core/`, `services/`, `gui/`, `utils/`, `tests/` at root level
- Additional `watermark_remover/` subpackage for CLI
- Config via YAML with `get_config()` function
- Logger singleton pattern with `get_logger()`

---

## Work Objectives

### Core Objective
Replace the existing AGENTS.md with a comprehensive, accurate guide based on actual codebase patterns.

### Concrete Deliverables
- `E:\op\op3\watermark_remover\AGENTS.md` - Updated with accurate information

### Definition of Done
- [ ] AGENTS.md contains accurate build/test commands verified from codebase
- [ ] Code style guidelines match actual code patterns
- [ ] Module structure reflects actual directory layout
- [ ] No references to non-existent Cursor/Copilot rules

### Must Have
- Accurate pytest commands for running single tests
- Correct module structure documentation
- Code style guidelines matching actual code

### Must NOT Have (Guardrails)
- References to non-existent Cursor/Copilot rules files
- Inaccurate test file paths (current AGENTS.md references `test_image_processor.py` which doesn't exist)
- Placeholder content without verification

---

## Verification Strategy

### Test Decision
- **Infrastructure exists**: YES (pytest)
- **Automated tests**: None needed (documentation update)
- **Agent-Executed QA**: YES

### Agent-Executed QA Scenarios

```
Scenario: Verify AGENTS.md contains accurate test commands
  Tool: Bash
  Steps:
    1. grep -q "pytest tests/test_batch_executor.py::test_run_batch_basic" AGENTS.md
    2. Assert: Exit code 0 (pattern found)
  Expected Result: AGENTS.md contains accurate single test command
  Evidence: Command output

Scenario: Verify AGENTS.md does not reference non-existent files
  Tool: Bash
  Steps:
    1. grep "test_image_processor.py::test_remove_watermark" AGENTS.md
    2. Assert: Exit code 1 (pattern NOT found)
  Expected Result: No references to non-existent test files
  Evidence: Command output
```

---

## TODOs

- [ ] 1. Update AGENTS.md with improved content

  **What to do**:
  - Replace entire AGENTS.md content with improved version
  - Include accurate build/test commands from codebase analysis
  - Document actual module structure (core/, services/, gui/, utils/, tests/)
  - Add testing patterns section with pytest examples
  - Include dataclass usage patterns
  - Document configuration management approach

  **Must NOT do**:
  - Reference non-existent Cursor/Copilot rules files
  - Use inaccurate test file paths
  - Include placeholder content

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Single file update with prepared content
  - **Skills**: None required
    - Simple file write operation

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Sequential
  - **Blocks**: None
  - **Blocked By**: None

  **References**:
  - `E:\op\op3\watermark_remover\AGENTS.md` - Current file to improve
  - `E:\op\op3\watermark_remover\tests\test_batch_executor.py` - Actual test patterns
  - `E:\op\op3\watermark_remover\utils\__init__.py` - Module export patterns
  - `E:\op\op3\watermark_remover\core\image_processor.py` - Code style examples
  - `E:\op\op3\watermark_remover\utils\exceptions.py` - Exception hierarchy

  **Acceptance Criteria**:
  - [ ] AGENTS.md updated with ~150 lines of content
  - [ ] Contains section 1) Build, lint, test commands with accurate pytest syntax
  - [ ] Contains section 2) Code style guide with naming, types, docs, errors
  - [ ] Contains section 3) Module structure with actual directory layout
  - [ ] Contains section 4) Testing strategy with pytest patterns
  - [ ] Contains section 5) Dataclass usage patterns
  - [ ] Contains section 6) Configuration management
  - [ ] No references to non-existent Cursor/Copilot rules

  **Commit**: YES
  - Message: `docs: improve AGENTS.md with accurate codebase patterns`
  - Files: `AGENTS.md`
  - Pre-commit: None required

---

## Success Criteria

### Verification Commands
```bash
# Verify file exists and has content
test -f AGENTS.md && wc -l AGENTS.md

# Verify key sections exist
grep -q "pytest tests/test_batch_executor.py::test_run_batch_basic" AGENTS.md
grep -q "WatermarkRemoverError" AGENTS.md
grep -q "dataclass" AGENTS.md
```

### Final Checklist
- [ ] All "Must Have" present
- [ ] All "Must NOT Have" absent
- [ ] File is approximately 150 lines
