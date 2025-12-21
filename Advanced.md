# Advanced Claude Code Features

This document covers advanced Claude Code capabilities for enhancing development workflow in this project.

---

## Table of Contents

1. [Hooks - Automated Workflow](#hooks---automated-workflow)
2. [Self-Documenting with CLAUDE.md](#self-documenting-with-claudemd)
3. [Session Tracking & Changelog](#session-tracking--changelog)
4. [Claude Web Integration](#claude-web-integration)
5. [Quick Start Commands](#quick-start-commands)

---

## Hooks - Automated Workflow

Hooks are shell commands that execute at specific points in Claude Code's lifecycle. They provide deterministic control over behavior.

### Setup

Run `/hooks` in Claude Code to configure, or add directly to `.claude/settings.json`:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "npx prettier --write \"$(jq -r '.tool_input.file_path')\" 2>/dev/null || true"
          }
        ]
      }
    ],
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "echo '=== Session Started ===' >> .claude/session-log.txt && date >> .claude/session-log.txt"
          }
        ]
      }
    ],
    "SessionEnd": [
      {
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/generate-changelog.sh"
          }
        ]
      }
    ]
  }
}
```

### Available Hook Events

| Event | When It Fires | Use Case |
|-------|---------------|----------|
| `PreToolUse` | Before any tool call | Block/validate commands |
| `PostToolUse` | After tool completes | Auto-format, lint, log |
| `SessionStart` | Session begins | Load context, setup env |
| `SessionEnd` | Session ends | Generate changelog, cleanup |
| `UserPromptSubmit` | User submits prompt | Validate, inject context |

### Recommended Hooks for This Project

Create `.claude/hooks/generate-changelog.sh`:

```bash
#!/bin/bash
# Auto-generate changelog entry after each Claude session

DATE=$(date +"%Y-%m-%d %H:%M")
CHANGELOG=".claude/CHANGELOG.md"

# Get git diff summary
CHANGES=$(git diff --stat HEAD 2>/dev/null | tail -1)

if [ -n "$CHANGES" ]; then
  echo "" >> $CHANGELOG
  echo "## $DATE" >> $CHANGELOG
  echo "" >> $CHANGELOG
  echo "### Changes" >> $CHANGELOG
  git diff --name-only HEAD 2>/dev/null | while read file; do
    echo "- Modified: \`$file\`" >> $CHANGELOG
  done
  echo "" >> $CHANGELOG
  echo "Stats: $CHANGES" >> $CHANGELOG
fi
```

Make it executable:

```bash
chmod +x .claude/hooks/generate-changelog.sh
```

---

## Self-Documenting with CLAUDE.md

The `CLAUDE.md` file system provides persistent memory across Claude sessions.

### Memory Hierarchy

| Level | File | Scope |
|-------|------|-------|
| Project | `./CLAUDE.md` | Team-wide, committed to git |
| Rules | `.claude/rules/*.md` | Modular, path-scoped rules |
| Local | `./CLAUDE.local.md` | Personal, gitignored |
| User | `~/.claude/CLAUDE.md` | All your projects |

### Path-Scoped Rules

Create focused rule files in `.claude/rules/`:

**`.claude/rules/api.md`**

```markdown
---
paths: app/api/**/*.ts
---

# API Route Standards

- All API routes must validate query parameters
- Return proper HTTP status codes (400, 404, 500)
- Include error messages in response body
- Log errors to console in development
```

**`.claude/rules/components.md`**

```markdown
---
paths: components/**/*.tsx
---

# Component Standards

- Use functional components with TypeScript
- Props interface must be defined and exported
- Include JSDoc comments for complex components
- Use Tailwind CSS for styling
```

### Session Documentation Template

Add to `CLAUDE.md` for automatic session tracking:

```markdown
## Session Log

Claude will document significant changes at the end of each session:

### Template

- **Date**: [Auto-filled]
- **Features Added**: [List]
- **Bugs Fixed**: [List]
- **Files Modified**: [List]
- **Next Steps**: [Recommendations]
```

---

## Session Tracking & Changelog

### Automatic Checkpointing

Claude Code automatically captures file state before each edit. Access with:

- `Esc Esc` - Open rewind menu
- `/rewind` - Slash command alternative

### Creating a Session Changelog

Create `.claude/CHANGELOG.md` to track all Claude sessions:

```markdown
# Claude Code Session Changelog

This file is auto-updated by Claude Code hooks after each session.

---

## 2024-XX-XX HH:MM

### Changes

- Modified: `file1.ts`
- Modified: `file2.tsx`

Stats: 2 files changed, 45 insertions(+), 12 deletions(-)

---
```

### Manual Session Summary Command

Ask Claude to generate a session summary anytime:

> "Summarize all changes made in this session and add to .claude/CHANGELOG.md"

---

## Claude Web Integration

Claude Code can interact with web content for research and testing.

### Use Cases for This Project

1. **API Documentation Lookup**
   - Fetch latest Next.js docs for API routes
   - Research SQLite/Prisma documentation

2. **Testing External APIs**
   - Verify geocoding API responses
   - Test restaurant data sources

3. **Competitive Research**
   - Analyze similar restaurant finder apps
   - Review UX patterns

### Example Workflow

```text
User: "Look up the Haversine formula and verify our implementation"

Claude: [Uses WebSearch to find authoritative sources]
        [Compares with utils/distance.ts implementation]
        [Reports any discrepancies]
```

---

## Quick Start Commands

```bash
# Initialize Claude Code hooks
mkdir -p .claude/hooks
# Add settings.json as shown above

# View Claude Code costs
# Run /cost in Claude Code

# Check loaded memories
# Run /memory in Claude Code

# Rewind changes
# Press Esc Esc or run /rewind
```

---

## Related Documentation

- [api-endpoints.md](./api-endpoints.md) - PRD for Reservations & Reviews (Next.js API routes + SQLite)
- [fastapi-backend.md](./fastapi-backend.md) - FastAPI backend alternative (Python + SQLite)
