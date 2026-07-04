# phonecli

Coordinate-based iOS phone agent toolkit. Uses WebDriverAgent (WDA) for device
control, LLM/VLM for understanding and classification, and app maps for
deterministic macro routing.

```
┌──────────────┐     subprocess      ┌─────────────────────────────────────┐
│  agent.py    │ ──────────────────→ │  cli.py                             │
│  loop/state  │                     │  ├── device/  screenshot, tap, ...  │
│  macro/VLM   │ ←──── JSON ──────── │  ├── macro/   build, run, validate  │
│  screen ID   │                     │  ├── llm/     map-task, xml-verify  │
└──────────────┘                     │  └── vlm/     act, verify           │
                                     └────────────────┬────────────────────┘
┌──────────────┐                                      │ HTTP
│  daemon.py   │ ─── REPL loop ───→                   ▼
│  memory.py   │   multi-app maps      ┌──────────────────────┐
└──────────────┘                       │  WebDriverAgent       │
                                       │  on iOS device        │
┌──────────────────────────────────┐   └──────────────────────┘
│  profile_builder.py              │
│  build_map.py  validate_map.py   │
│  sanitize_map.py                 │
│  5-stage auto-build pipeline     │
└──────────────────────────────────┘
```

---

## 1. Setup

### Prerequisites

```bash
brew install libimobiledevice
pip install requests openai click pyyaml
```

### Install WebDriverAgent

WebDriverAgent (WDA) is an iOS test runner that exposes an HTTP API for device
control — the foundation everything else builds on.

**Step 1: Clone and bootstrap**

```bash
brew install carthage            # required by bootstrap.sh
git clone https://github.com/appium/WebDriverAgent.git
cd WebDriverAgent
./Scripts/bootstrap.sh
```

**Step 2: Open in Xcode**

```bash
open WebDriverAgent.xcodeproj
```

**Step 3: Configure signing**

Both the `WebDriverAgentLib` and `WebDriverAgentRunner` targets need a signing
team. If you don't have a paid Apple Developer account, use your personal Apple ID
(free tier works fine):

1. In Xcode, select the **WebDriverAgentLib** target → **Signing & Capabilities**
2. Check **Automatically manage signing**, select your Team
3. Repeat for the **WebDriverAgentRunner** target
4. If the bundle identifier conflicts, change it (e.g. prefix with your name: `com.yourname.WebDriverAgentRunner`)

**Step 4: Build & Run**

1. Select the **WebDriverAgentRunner** scheme at the top of Xcode
2. Choose your connected iOS device as the destination
3. Press **Cmd+U** (Product → Test) to build and launch WDA

On the first run, iOS blocks the developer certificate. Go to **Settings →
General → VPN & Device Management → your Apple ID → Trust**, then re-run.

**Step 5: Port forwarding**

WDA listens on the device. Use `iproxy` to forward it to localhost:

```bash
brew install libimobiledevice   # provides iproxy
iproxy 8100 8100 &
```

**Step 6: Verify**

```bash
curl http://localhost:8100/status
# → {"value": {"state": "success", ...}, "sessionId": "..."}
```

If you see a JSON response with `"state": "success"`, WDA is ready.

> **Note for free accounts**: Free provisioning profiles expire after 7 days.
> You'll need to rebuild WDA in Xcode each week. A paid developer account
> removes this restriction.

### Configure LLM/VLM

```bash
# Option A: OpenRouter (text + vision)
export API_KEY="sk-or-v1-..."
export API_BASE="https://openrouter.ai/api/v1"
export MODEL_NAME="qwen/qwen3.7-plus"

# Option B: DeepSeek (text-only, for build)
export API_KEY="sk-..."
export API_BASE="https://api.deepseek.com/v1"
export MODEL_NAME="deepseek-v4-flash"

# Option C: Local
export API_BASE="http://localhost:8002/v1"
export MODEL_NAME="Qwen/Qwen2.5-VL-7B-Instruct"
```

### Quick test

```bash
python phonecli/cli.py device info
# → {"status": "ok", "width": 402, "height": 874, ...}
```

> All commands in this README are run from the **repo root** (the directory
> containing `phonecli/`). If you prefer to `cd phonecli` first, drop the
> `phonecli/` prefix from command paths and adjust output paths accordingly.

---

## 2. Quick Start

> **Working directory**: all commands below are run from the repo root (the
> directory containing `phonecli/`). The CLI's default output paths use
> `phonecli/app_maps/` and `phonecli/profiles/` accordingly.

This 5-minute walkthrough takes you from nothing to a working phone agent.

### One-time setup

```bash
# Install dependencies
brew install libimobiledevice
pip install requests openai click pyyaml

# Configure your LLM (OpenRouter example)
export API_KEY="sk-or-v1-..."
export API_BASE="https://openrouter.ai/api/v1"
export MODEL_NAME="qwen/qwen3.7-plus"
```

Follow [Section 1 — Install WebDriverAgent](#install-webdriveragent) to get
WDA running on your device, then verify:

```bash
curl http://localhost:8100/status   # should return JSON with "state": "success"
```

### Build your first app map (~10 min)

```bash
python phonecli/cli.py macro auto-build -b com.apple.Preferences -a Settings
```

This crawls the Settings app and generates an app map. For details see
[Section 3 — Build an app map](#3-build-an-app-map).

### Run your first task

```bash
python phonecli/run.py --task "Turn on airplane mode"
```

The agent auto-discovers all built app maps, decomposes the task, replays the
macro, and verifies with VLM.

### What's next

- **[Section 3](#3-build-an-app-map)**: Build maps for more apps
- **[Section 4](#4-run-tasks)**: One-shot mode, interactive daemon, cross-app tasks
- **[Section 7](#7-cli-reference)**: Full CLI command reference

---

## 3. Build an app map

### One command (recommended)

The `auto-build` command runs all 5 stages automatically:

```bash
python phonecli/cli.py macro auto-build \
    -b com.apple.mobilecal \
    -a Calendar \
    -o phonecli/app_maps/calendar_map.yaml \
    --classify --enrich --redact
```

### 5-stage pipeline

```
Stage 1: sample screen_0 → collect visible element texts (~1 min)
Stage 2: LLM generates app-specific profile (dynamic_patterns + preserve_navigation)
Stage 3: BFS crawl with profile + LLM classify + enrich (main build)
Stage 4: validate map for errors, data quality, profile effectiveness
Stage 5: sanitize — LLM batch-detects and replaces personal data
```

### Output files

| File | Path | Description |
|------|------|-------------|
| App map | `phonecli/app_maps/<app>_map.yaml` | Full navigation graph (screens, elements, macros) |
| Profile | `phonecli/profiles/<App>.yaml` | Filtering patterns for dynamic content |
| Checkpoint | `.checkpoints/<app>_checkpoint.json` | Resume file (auto-deleted on success) |

### Common bundle IDs

| App | Bundle ID |
|-----|-----------|
| Settings | `com.apple.Preferences` |
| Calendar | `com.apple.mobilecal` |
| Safari | `com.apple.mobilesafari` |
| 小红书 | `com.xingin.discover` |
| 微博 | `com.sina.weibo` |
| 京东 | `com.jingdong.app.mall` |
| 大众点评 | `com.dianping.dpscope` |
| foodpanda | `com.foodpanda.ios` |
| Music | `com.apple.Music` |

```bash
ideviceinstaller -l   # list installed apps
```

### Options

| Parameter | Default | Description |
|-----------|---------|-------------|
| `-b, --bundle-id` | *(required)* | iOS bundle ID |
| `-a, --app-name` | *(required)* | Human-readable name |
| `-o, --output` | `phonecli/app_maps/app_map.yaml` | Output path |
| `--max-screens` | `50` | Cap on screens |
| `--max-depth` | `3` | Max navigation depth |
| `--scroll-pages` | `3` | Scroll pages per screen |
| `--classify/--no-classify` | on | LLM stable/dynamic classification |
| `--enrich/--no-enrich` | on | LLM aliases, semantic types, descriptions |
| `--redact/--no-redact` | on | PII redaction |
| `-c, --checkpoint` | none | Enable checkpoint/resume |
| `-r, --resume` | none | Resume from checkpoint |

### Resume after interruption

```bash
# Initial run with checkpoint
python phonecli/cli.py macro auto-build -b com.sina.weibo -a 微博 \
    -c .checkpoints/weibo_checkpoint.json

# If interrupted (WDA timeout, network, etc.), resume:
python phonecli/cli.py macro auto-build -b com.sina.weibo -a 微博 \
    -c .checkpoints/weibo_checkpoint.json \
    -r .checkpoints/weibo_checkpoint.json
```

### App profile format

Profiles use regex patterns to filter dynamic content and a whitelist to preserve
navigation elements:

```yaml
app: Calendar
bundle_id: com.apple.mobilecal
dynamic_patterns:
  - '^\d+$'              # numbers (counts, timestamps)
  - '^.{8,}$'            # long text (post titles, descriptions)
preserve_navigation:
  - Today
  - Calendars
  - Add
```

### App map structure

```yaml
app: Calendar
package: com.apple.mobilecal
screen_w: 402
screen_h: 874
launch_behavior: always_home
common_tasks:
  - Create a new event
  - Check today's schedule
screens:
  - id: screen_0
    description: "Month view with navigation tabs"
    elements:
      - text: Today
        center: [0.1667, 0.9405]
        fixed: true
        leads_to: screen_4
        aliases: [current day, now, 今天]
        semantic_type: button
screen_macros:
  screen_0: [force_stop, launch]
  screen_4: [force_stop, launch, tap(67, 822)]
```

### Built-in maps

The package ships with pre-built maps for 8 apps:

| App | Screens | Elements | Edges |
|-----|---------|----------|-------|
| 微博 | 50 | 975 | 77 |
| foodpanda | 50 | 957 | 95 |
| Calendar | 50 | 948 | 88 |
| 京东 | 50 | ~700 | ~100 |
| Dianping | 50 | 501 | 70 |
| 小红书 | 50 | 405 | 142 |
| Music | 50 | ~500 | ~80 |
| Settings | 20 | ~200 | ~40 |

---

## 4. Run tasks

### Auto-discovery

`run.py` automatically discovers all `phonecli/app_maps/*.yaml` files. Simply run
without `--app-map`:

```bash
python phonecli/run.py --task "Turn on airplane mode"
```

### One-shot mode

```bash
# Auto-discover all maps
python phonecli/run.py --task "Turn on airplane mode" --max-rounds 25

# Explicit map (single or multi)
python phonecli/run.py --task "Turn on wifi" \
    --app-map phonecli/app_maps/settings_map.yaml

# Pure VLM mode (no maps)
python phonecli/run.py --task "Check battery level" --no-macro --max-rounds 30
```

### Interactive daemon

```bash
# Auto-discover all maps
python phonecli/run.py --interactive

# Explicit maps (multi-app)
python phonecli/run.py --interactive \
    --app-map phonecli/app_maps/settings_map.yaml \
    --app-map phonecli/app_maps/weibo_map.yaml

[phonecli] Task> Turn on Wi-Fi
[Agent] Macro replayed → Wi-Fi is ON

[phonecli] Task> memory
  Tasks: 5 (OK 5 FAIL 0)
  Operations: op_wifi_on 3x (8s avg)
```

### Cross-app tasks

The agent automatically decomposes complex multi-app tasks via the Planner
(`llm plan` CLI command). No manual intervention needed:

```bash
python phonecli/run.py --task "先小红书搜索，再京东比价，最后备忘录记录" --max-rounds 30
```

The Planner breaks the task into single-app subtasks, executes them sequentially,
and skips LLM mapping for apps without loaded maps (falls back to VLM).

### REPL commands

| Command | Action |
|---------|--------|
| `<any task>` | Execute on device |
| `memory` | Show task history and op stats |
| `forget` | Clear session dialogue memory |
| `quit` | Exit daemon |

---
## 5. Agent features

The agent (`agent.py`) orchestrates task execution via a hybrid approach:

| Feature | Description |
|---------|-------------|
| **Macro routing** | Deterministic replay of pre-built app map operations |
| **Cross-app awareness** | Detects foreground app via WDA, injects into VLM context |
| **Smart Macro/VLM split** | Auto-upgrades OP to MACRO_VLM when task requires search/input |
| **Action feedback** | Pixel-diffs screenshots after each action, warns VLM on no effect |
| **Screen identification** | Matches XML dump against app maps to provide nav targets |
| **Available apps list** | Injects known apps into VLM context for reliable launch() |
| **Loop detection** | Aborts when same action type repeats 3x with no progress |
| **VLM escalation** | Auto-injects home() after 3 consecutive VLM parse failures |
| **Planner** | Decomposes cross-app tasks into single-app subtasks |

---

## 6. Evaluation

```bash
python phonecli/eval.py --app-map phonecli/app_maps/settings_map.yaml
python phonecli/eval.py --app-map phonecli/app_maps/settings_map.yaml --tasks 1,3,5
python phonecli/eval.py --no-macro --max-rounds 30   # pure VLM
python phonecli/eval.py --app-map phonecli/app_maps/settings_map.yaml -o results.json
```

---

## 7. CLI reference

### Device operations

```bash
python phonecli/cli.py device info
python phonecli/cli.py device screenshot -o /tmp/s.png
python phonecli/cli.py device xml -o /tmp/dump.xml
python phonecli/cli.py device tap 195 420
python phonecli/cli.py device swipe 195 600 195 200
python phonecli/cli.py device text "hello world"
python phonecli/cli.py device launch Settings
python phonecli/cli.py device back
python phonecli/cli.py device home
python phonecli/cli.py device long-press 195 420 -d 3000
```

### Macro operations

```bash
python phonecli/cli.py macro list -m phonecli/app_maps/settings_map.yaml
python phonecli/cli.py macro run -m phonecli/app_maps/settings_map.yaml --op-id op_wifi_on
python phonecli/cli.py macro sample -b com.apple.mobilecal -a Calendar
python phonecli/cli.py macro validate -m phonecli/app_maps/calendar_map.yaml
python phonecli/cli.py macro sanitize -m phonecli/app_maps/calendar_map.yaml
```

### LLM operations

```bash
# Map a task to an app map operation
python phonecli/cli.py llm map-task -m phonecli/app_maps/settings_map.yaml -t "Turn on wifi"
# Verify task completion from XML accessibility tree
python phonecli/cli.py llm xml-verify -t "Check wifi" --xml-file /tmp/dump.xml
# Decompose a multi-app task into subtasks
python phonecli/cli.py llm plan -t "先小红书搜索，再京东比价" \
    -m phonecli/app_maps/xiaohongshu_map.yaml \
    -m phonecli/app_maps/jd_map.yaml
```

### VLM operations

```bash
python phonecli/cli.py vlm act -t "Open Settings" -s /tmp/s.png
python phonecli/cli.py vlm verify -t "Is wifi on?" -s /tmp/s.png
```

---

## 8. Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `API_KEY` | `EMPTY` | API key (fallback for all) |
| `API_BASE` | `http://localhost:8002/v1` | API base (fallback) |
| `MODEL_NAME` | `Qwen/Qwen2.5-3B-Instruct` | Model name (fallback) |
| `PHONECLI_LLM_API_KEY` | *(falls back)* | Text LLM override |
| `PHONECLI_LLM_API_BASE` | *(falls back)* | Text LLM endpoint |
| `PHONECLI_LLM_MODEL` | *(falls back)* | Text LLM model |
| `PHONECLI_VLM_API_KEY` | *(falls back)* | Vision model override |
| `PHONECLI_VLM_API_BASE` | *(falls back)* | Vision model endpoint |
| `PHONECLI_VLM_MODEL` | *(falls back)* | Vision model |
| `PHONECLI_WDA_URL` | `http://localhost:8100` | WDA URL |
| `PHONECLI_TASK_DIR` | `./phonecli_logs` | Log directory |

---

## 9. Troubleshooting

### WDA not connecting

```bash
curl http://localhost:8100/status
# curl: (7) Failed to connect to localhost port 8100
```

- Check `iproxy` is running: `pgrep iproxy`. If not, restart it: `iproxy 8100 8100 &`
- Check USB connection and that the device is unlocked
- Rebuild WDA in Xcode (Cmd+U) — the session may have died

### Code signing expired

If Xcode reports a signing error, your free provisioning profile has likely
expired (7-day limit). Re-open WebDriverAgent in Xcode, go to
**Signing & Capabilities**, and re-enable automatic signing. Xcode will
regenerate the profile.

### WDA session lost mid-run

```
[WDA] session timed out / no active session
```

WDA sessions can time out after inactivity. The agent creates sessions on demand,
but long pauses may cause timeouts. Restart WDA (Cmd+U in Xcode), then re-run.

### iproxy port already in use

```
bind: Address already in use
```

Kill the old iproxy process:

```bash
pkill iproxy
iproxy 8100 8100 &
```

### VLM parse failures

```
[Agent] VLM parse failed 3x consecutively — injecting home()
```

The VLM occasionally returns malformed coordinates. The agent auto-injects
`home()` after 3 consecutive parse failures as a recovery strategy. If this
happens frequently, try a more capable vision model or check your API key.

### Macro replay wrong screen

If a macro navigates to the wrong screen, the app map may be stale (the app UI
has changed since the map was built). Rebuild the map:

```bash
python phonecli/cli.py macro auto-build -b <bundle-id> -a <AppName>
```

### LLM connection errors

```
openai.APIConnectionError / openai.RateLimitError
```

- Verify your `API_KEY` is valid and `API_BASE` is correct
- Check rate limits or switch to a different provider
- For local models, ensure the vLLM/Ollama server is running

---

## 10. Architecture

```
phonecli/
├── device.py           iOS WDA HTTP API (screenshot, tap, swipe, launch, …)
├── app_map.py          YAML loader, screen identification, relative macros
├── build_map.py        BFS app crawler (LLM classify, fixed/scrollable, PII)
├── profile_builder.py  5-stage pipeline orchestrator (sample → profile → build)
├── validate_map.py     Stage 4: map validation (errors, data quality, profile)
├── sanitize_map.py     Stage 5: batch LLM PII detection and replacement
├── llm_client.py       OpenAI-compatible API (text + vision)
├── prompts.py          System prompts for all LLM/VLM tasks
├── cli.py              Click CLI — 4 groups (device/macro/llm/vlm)
├── agent.py            PhoneAgent loop (macro routing, VLM, screen ID)
├── daemon.py           Interactive REPL loop (session reuse, multi-map)
├── memory.py           DialogueMemory + UserMemory (persistent, macro-aware)
├── eval.py             Batch evaluation with independent VLM judge
├── run.py              Entry point (one-shot / interactive)
├── app_maps/           Built-in app maps (8 apps)
└── profiles/           App filtering profiles (8 apps)
```
