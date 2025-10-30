---
applyTo: '**'
description: "Guidelines for how AI agents should implement changes"
---

# Implementation Workflow for AI Agents

## Core Principles

When implementing features or fixes, AI agents **MUST** follow this workflow:

1. **Use Sub-Agents for Implementation**: All implementation tasks must be delegated to sub-agents using the `runSubagent` tool
2. **Review Before Proceeding**: Each sub-agent's work must be thoroughly reviewed before starting the next task
3. **Follow Version Control Guidelines**: All commits must follow the guidelines in `version-control.instructions.md`

## Workflow Steps

### 1. Planning Phase

Before any implementation:
- Break down the user's request into discrete, actionable tasks
- Identify dependencies between tasks
- Determine the order of implementation
- Document the plan in `.working-memory/` if the task is complex

### 2. Implementation Phase

For each task:

**a. Delegate to Sub-Agent**
- Use `runSubagent` with a clear, detailed prompt
- Specify exactly what needs to be implemented
- Include context about the codebase, patterns to follow, and testing requirements
- Clearly state whether the sub-agent should write code or just research

Example:
```
You are implementing the Library class for bundling prompts in the Pareidolia project.

Context: Pareidolia uses dataclasses with type hints, follows Google-style docstrings, and requires pytest tests for all features.

Task:
1. Create src/pareidolia/core/library.py with a Library dataclass
2. Implement validation for library names
3. Add tool-specific prefix mapping (Claude Code, GitHub Copilot)
4. Create comprehensive unit tests in tests/unit/test_library.py
5. Ensure all code passes ruff and mypy checks

Return: A summary of files created/modified and test results.
```

**b. Review Sub-Agent's Work**
- Read all files the sub-agent created or modified
- Verify code quality (type hints, docstrings, error handling)
- Run tests: `uv run pytest`
- Run linters: `uv run ruff check .` and `uv run mypy src/`
- Check that version control guidelines were followed
- If issues are found, delegate corrections to another sub-agent or fix them directly

**c. Verify Integration**
- Ensure the new code integrates properly with existing code
- Run the full test suite
- Test any affected CLI commands manually if needed

### 3. Commit Phase

After reviewing and verifying the sub-agent's work:
- Stage related changes together (implementation + tests)
- Commit with proper message following `version-control.instructions.md`
- Set author to Copilot with co-author trailer
- Ensure commit message explains "why" not just "what"

### 4. Iteration

If multiple tasks are needed:
- Complete one task fully (implement → review → commit) before starting the next
- Keep commits atomic and logical
- Maintain the codebase in a working state after each commit

## Review Checklist

Before accepting a sub-agent's work, verify:

- [ ] All code has proper type hints
- [ ] All public APIs have Google-style docstrings
- [ ] Tests are included and passing
- [ ] Code passes `ruff check .`
- [ ] Code passes `mypy src/`
- [ ] Commit messages follow Linux kernel format
- [ ] Commits are authored by Copilot with co-author trailer
- [ ] Code follows project patterns (see AGENTS.md)
- [ ] Error handling is appropriate
- [ ] Changes are atomic and logical

## When NOT to Use Sub-Agents

Sub-agents are required for implementation tasks, but not for:
- Simple questions about the codebase
- Reading files or searching code
- Running tests or linters
- Trivial one-line fixes
- Documentation-only changes

## Error Recovery

If a sub-agent's work has issues:
1. Document what went wrong
2. Either fix directly (for small issues) or delegate to another sub-agent (for larger issues)
3. Re-run tests and linters
4. Only proceed when all issues are resolved

## Summary

**Key Rule**: Implementation work MUST be done by sub-agents, and their output MUST be reviewed before proceeding to the next task. This ensures code quality, proper testing, and adherence to project standards.