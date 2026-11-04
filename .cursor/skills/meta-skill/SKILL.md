---
name: meta-skill
description: Creates new Agent Skills following best practices. Use when you want to create a new skill, extend agent capabilities, or package domain expertise into a reusable skill.
---

# Create New Skills

## Instructions

This skill guides you through creating new Agent Skills for Cursor.

### Understanding Skills

**What is a Skill?**
- A directory containing a `SKILL.md` file with YAML frontmatter
- Instructions loaded on-demand when relevant
- Optional supporting files (scripts, documentation, templates)

**Progressive Disclosure (3 Levels):**
1. **Metadata** (always loaded): `name` and `description` in YAML frontmatter
2. **Instructions** (loaded when triggered): Main body of SKILL.md
3. **Resources** (loaded as needed): Additional files, scripts, templates

### Skill Creation Workflow

#### Step 1: Define the Skill's Purpose

Ask the user:
1. What task or domain should this skill cover?
2. When should the skill be triggered?
3. What expertise or workflows need to be captured?
4. Does it need scripts, templates, or other resources?

#### Step 2: Create the Skill Directory

Create skills in the project's `.cursor/skills/` directory:

```bash
mkdir -p .cursor/skills/<skill-name>
```

Naming conventions: lowercase with hyphens, descriptive but concise.

#### Step 3: Design the SKILL.md Structure

Every skill must have:
```yaml
---
name: Your Skill Name
description: Brief description including WHAT it does and WHEN to use it
---

# Your Skill Name

## Instructions
[Clear, step-by-step guidance]

## Examples
[Concrete usage examples]
```

Frontmatter requirements:
- `name`: Required, max 64 characters
- `description`: Required, max 1024 characters — include both what it does AND trigger phrases

#### Step 4: Write the Instructions

Structure as:
1. **Prerequisites** — dependencies, tools, environment
2. **Workflow** — numbered step-by-step process
3. **Supporting Details** — additional context, error handling

Best practices:
- Use clear, actionable language
- Number sequential steps
- Include code blocks with commands
- Reference supporting files with relative links
- Keep focused on one capability

#### Step 5: Write Examples

Provide 2-4 concrete examples showing different use cases, inputs, and expected outcomes.

#### Step 6: Add Supporting Files (Optional)

- Additional instructions in `.md` files
- Scripts in `scripts/` directory
- Templates in `templates/` directory
- Make scripts executable

#### Step 7: Test the Skill

1. Verify file structure exists
2. Check YAML frontmatter is valid
3. Test with relevant queries matching the description
4. Iterate: refine description if skill doesn't trigger, clarify instructions if unclear

### Best Practices Summary

- Description: Include BOTH what it does AND when/how to trigger it
- Instructions: Keep under 5k tokens; split complex content into linked files
- Scope: One skill = one capability; make focused, composable skills
- File references: Use relative paths from skill root

## Examples

### Example 1: Simple Code Review Skill

User request: "Create a skill that reviews Python code for best practices"

1. Create directory: `.cursor/skills/python-code-review/`
2. Write SKILL.md with name, description mentioning "Python", "PEP 8", "code review"
3. Add workflow: read files, check PEP 8, identify security issues, suggest improvements
4. Add examples for single file, multi-file, and focused security reviews

### Example 2: Data Analysis Skill with Scripts

User request: "Build a skill for analyzing CSV data"

1. Create structure with `scripts/` and `templates/` subdirectories
2. Write SKILL.md referencing analysis and visualization scripts
3. Create Python scripts with proper dependency declarations
4. Add examples for basic statistics, visualizations, and custom reports

### Example 3: Multi-File Documentation Skill

User request: "Create a skill for technical docs with our style guide"

1. Create structure with `templates/`, `examples/`, `guidelines/`
2. Write SKILL.md with progressive disclosure — only load relevant guidelines
3. Add templates for different doc types
4. Add examples for API docs, user guides, architecture records

### MAT repo: adoption and operator skills

When a new skill wraps **shipped MAT scripts** (for example under `scripts/adoption/`, `scripts/doctor.sh`, or `mat-legacy-fingerprints.py`):

- Follow [`docs/MAINTAINER.md`](../../../.mat/docs/MAINTAINER.md#documentation-and-skill-inventory-hygiene) and the **Inventory hygiene** subsection in [`AGENTS.md`](../../../AGENTS.md).
- Update [`docs/reference/components.md`](../../../.mat/docs/components.md) when the skill represents a first-class operator capability.
- Prefer linking to canonical command docs under `.cursor/commands/mat-*.md` instead of duplicating long procedural text in the skill body.
