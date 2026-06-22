# OpenPhone CLI

Agent CLI for iOS device automation. Two modes in one tool:

- **Agent-driven mode** — external AI (Claude Code, Codex, etc.) controls the device step-by-step.
- **Autonomous mode** — built-in VLM executes tasks end-to-end via the Ralph Loop.

## Quick Start

### Prerequisites

- **iOS device** with [WebDriverAgent](https://github.com/appium/WebDriverAgent) (WDA) running and accessible at `http://localhost:8100`
- **Python 3.10+** with dependencies installed:

```bash
pip install -r requirements.txt
```

The CLI core (agent-driven commands) only needs `requests` and `Pillow`. The autonomous mode (`run`, `daemon`, `learn`) additionally needs `backoff`, `openai`, `opencv-python`, and `zhipuai`.

### Verify

```bash
python -m cli.main --version
```

To use the shorter `openphone` command, create a shell alias:

```bash
alias openphone='python -m cli.main'
```

## Commands

### Agent-Driven Mode

For external AI harness to inspect and interact with iOS devices.

```bash
# Launch an app
python -m cli.main open Safari

# Capture screen + find interactive elements
python -m cli.main snapshot --json

# Tap by element ref, coordinates, or fraction
python -m cli.main tap @e3         # element from snapshot
python -m cli.main tap 200,300     # pixel coordinates
python -m cli.main tap 0.5,0.5     # screen fraction

# Type text
python -m cli.main type "hello"

# Swipe a direction
python -m cli.main swipe up        # up / down / left / right

# System keys
python -m cli.main press home
python -m cli.main press back

# Timing and keyboard control
python -m cli.main wait 1.5               # wait for animation / page load
python -m cli.main keyboard               # dismiss the on-screen keyboard
```

**Supported app names** for the `open` command: Safari, Settings, Messages, Mail, Photos, Camera, Clock, Calendar, Maps, Music, App Store, Notes, Reminders, Weather, Calculator, Contacts, FaceTime, Phone, WeChat, Feishu, Meituan, and more. To add custom apps, edit `APP_PACKAGES_IOS` in `ios_agent/actions.py`.

### Autonomous Mode

Built-in VLM plans and executes tasks with the Ralph Loop (plan → act → evaluate → fix → repeat).

```bash
# Execute a single task
python -m cli.main run "打开微信，查看最近5条对话" \
    --openrouter --model-name "z-ai/glm-4.6v"

# Interactive daemon (continuous task input)
python -m cli.main daemon --openrouter

# Record a human demo and learn from it
python -m cli.main learn Safari --describe "Send a message"
```

### Memory Management

```bash
python -m cli.main memory show                      # user profile
python -m cli.main memory list                      # all learned lessons
python -m cli.main memory list --app WeChat         # filter by app
python -m cli.main memory query "my name"           # search memories
```

## Snapshot Output

`snapshot --json` returns:

```json
{
  "success": true,
  "screenshot": "<base64 png>",
  "width": 1179,
  "height": 2556,
  "app": "Safari",
  "elements": [
    {
      "ref": "@e1",
      "type": "XCUIElementTypeButton",
      "name": "搜索",
      "label": "Search",
      "bounds": {"x": 300, "y": 100, "width": 80, "height": 44},
      "center": {"x": 340, "y": 122},
      "enabled": true
    }
  ],
  "element_count": 42
}
```

Use `ref` values in subsequent `tap` commands. Re-snapshot after each action to verify results and find new element refs.

## Global Flags

| Flag | Description |
| --- | --- |
| `--json` | Machine-readable JSON output |
| `--wda-url` | WebDriverAgent URL (default: `http://localhost:8100`) |
| `--session-id` | WDA session ID (auto-created if omitted) |

## Autonomous Mode Flags

| Flag | Description |
| --- | --- |
| `--openrouter` | Use OpenRouter cloud VLM |
| `--model-name` | Model name (default: `z-ai/glm-4.6v`) |
| `--max-rounds` | Max action rounds per task (default: 100) |
| `--max-fix-retries` | Fix retries per subtask (default: 3) |
| `--no-memory` | Disable user profile memory |
| `--no-experience` | Disable experience learning |

See `python -m cli.main run --help` for the full list.

## Environment Variables

```bash
WDA_URL=http://localhost:8100
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_MODEL=z-ai/glm-4.6v
```

## Agent Workflow

A typical AI agent session:

```
1. open <app>                  # launch target
2. wait 1.0                    # wait for app to load
3. snapshot --json             # get screen state + elements
4. analyze elements, decide    # AI reasoning
5. tap @e5                     # interact
6. keyboard                    # dismiss keyboard if visible
7. wait 0.5                    # wait for transition
8. snapshot --json             # verify result
9. repeat 4-8 until done
```

## Architecture

```
cli/main.py          ← entry point, argparse routing
  ├── commands/device.py    ← agent-driven (snapshot, tap, type, swipe, press, open, wait, keyboard)
  ├── commands/run.py       ← autonomous (run, daemon, learn)
  └── commands/memory.py    ← memory (show, list, query)
```

New code lives in `cli/`. Existing code is imported with minimal touch-ups:
- `PhoneClaw/connection.py` — re-exports from `ios_agent.connection` (deduplicated)
- `ios_agent/__init__.py` — lazy imports for optional-heavy modules (cv2, zhipuai)

## Dependencies

See the project root `requirements.txt`. Core CLI (agent-driven commands) needs: `requests`, `Pillow`. Autonomous mode (`run`, `daemon`, `learn`) additionally needs: `backoff`, `openai`, `opencv-python`, `zhipuai`.
