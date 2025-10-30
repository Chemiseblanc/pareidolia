---
applyTo: '**'
---

# Git Workflow Guidelines

## Branching Strategy

- `master`: Main development branch (stable)
- `feature/<name>`: Feature branches for new functionality
- `bugfix/<name>`: Bug fix branches
- `refactor/<name>`: Code refactoring branches

## Commit Message Guidelines

Follow Linux kernel commit message format (without sign-off):

```
<component>: <short summary> (50 chars max)

<Detailed description wrapped at 72 characters. Explain the problem
being solved and why this change is being made. Focus on the "why"
rather than the "how".>

<Additional paragraphs as needed>

- Bullet points are acceptable
- Use hyphens or asterisks for bullets

Co-authored-by: <Current User Name> <user@email.com>
```

## Commit Authorship

AI agents should set commits to be authored by Copilot with proper attribution:

- **Author**: Set to `Copilot <Copilot@users.noreply.github.com>`
- **Co-authored-by**: Add trailer with current git user's name and email

This can be done with:
```bash
# Get current user info
CURRENT_USER=$(git config user.name)
CURRENT_EMAIL=$(git config user.email)

# Commit with Copilot as author and add co-author trailer
git commit --author="Copilot <Copilot@users.noreply.github.com>" \
  -m "<component>: <short summary>

<Detailed description>

Co-authored-by: $CURRENT_USER <$CURRENT_EMAIL>"
```

**Components** might include:
- `cli`: Command-line interface changes
- `core`: Core functionality
- `templates`: Template engine changes
- `generators`: Prompt generation logic
- `tests`: Test suite changes
- `docs`: Documentation updates
- `build`: Build system or dependency changes

**Examples**:

```
cli: add library creation command

Implement the 'library create' subcommand to bundle related prompts
into tool-specific collections. This allows users to generate multiple
prompts with consistent prefixes for different AI tools.

- Add library subparser to CLI
- Implement naming convention mapping for tools
- Add validation for library names

Co-authored-by: Matthew Gibson <matt@mgibson.ca>
```

```
templates: integrate jinja2 template engine

Add Jinja2 support for compiling persona, task, and example fragments
into complete prompts. This provides flexible composition and enables
variable substitution in templates.

Co-authored-by: Matthew Gibson <matt@mgibson.ca>
```

## Commit Best Practices

- **Atomic commits**: Each commit should represent one logical change
- **Buildable commits**: Each commit should leave the codebase in a working state
- **Test with commits**: Add tests in the same commit as the feature when possible
- **Fix in place**: If you find an issue in your branch, amend or fixup rather than adding "fix" commits
