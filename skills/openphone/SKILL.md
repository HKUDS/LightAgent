---
name: openphone
description: Automation for iOS devices via the OpenPhone CLI. Use when the user asks to interact with an iPhone or iPad — opening apps, taking snapshots, tapping, typing, scrolling, reading the screen, or running autonomous phone tasks.
allowed-tools: Bash(python -m cli.main:*)
---

# OpenPhone

Router only. OpenPhone is an Agent CLI that provides two modes:
- **Agent-driven mode** — external AI (you) controls the device step-by-step.
- **Autonomous mode** — OpenPhone's built-in VLM executes complete tasks via the Ralph Loop.

The CLI entry point is `python -m cli.main`. For brevity these docs use `openphone` as a shorthand — replace with `python -m cli.main` or create a shell alias:
```bash
alias openphone='python -m cli.main'
```

## Prerequisites

The iOS device must have WebDriverAgent (WDA) running and accessible. Default: `http://localhost:8100`.

Verify: `python -m cli.main --version`

If WDA is not running, start it on the device first.

## Agent-driven workflow

```
python -m cli.main open <app>          # Launch the target app
python -m cli.main wait 1.0            # Wait for app to load / animation to finish
python -m cli.main snapshot --json     # Capture screen + interactive elements (returns JSON with @e1, @e2... refs)
python -m cli.main tap @e3             # Tap element by ref
python -m cli.main type "hello"        # Type text into focused input
python -m cli.main keyboard            # Dismiss the on-screen keyboard
python -m cli.main swipe up            # Scroll (up/down/left/right)
python -m cli.main press home          # Go to home screen
python -m cli.main press back          # Go back
```

The `snapshot --json` command returns:
- `screenshot`: base64-encoded PNG
- `elements[]`: list of `{ref, type, name, label, bounds, center, enabled}`
- `app`: current foreground app name

Use snapshot between actions to verify results and find next element refs.

## Autonomous-mode workflow

```
python -m cli.main run "Open WeChat and check my last 5 messages" --openrouter --model-name "z-ai/glm-4.6v"
python -m cli.main daemon --openrouter    # Interactive REPL for continuous tasks
python -m cli.main learn Safari           # Record a demo and extract navigation lessons
python -m cli.main memory show            # View persistent user profile
python -m cli.main memory list --app WeChat # View learned experience for an app
python -m cli.main memory query "my name" # Search memory for relevant info
```

## Commands reference

| Command | Args | Description |
|---------|------|-------------|
| `snapshot` | `[--json]` | Screenshot + UI hierarchy |
| `tap` | `<ref>` | Tap @eN, x,y, or 0.x,0.y |
| `type` | `<text>` | Type text |
| `keyboard` | | Dismiss on-screen keyboard |
| `swipe` | `<dir>` | Swipe up/down/left/right |
| `press` | `<key>` | Press home or back |
| `open` | `<app>` | Launch app by name |
| `wait` | `<sec>` | Wait N seconds |
| `run` | `<task>` | Execute task autonomously |
| `daemon` | | Interactive REPL mode |
| `learn` | `[app]` | Record and learn from demo |
| `memory` | `show\|list\|query` | Manage memory |

All commands accept `--wda-url` and `--json` flags. Autonomous commands accept additional VLM configuration flags.
