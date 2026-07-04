"""Agent loop orchestrator — coordinates CLI calls for task execution.

Architecture (Approach A — thin CLI):
    Agent (this process)
    ├── subprocess.run("python cli.py llm map-task ...")   → task mapping
    ├── subprocess.run("python cli.py macro run ...")       → macro replay
    ├── subprocess.run("python cli.py device screenshot ...") → screenshot
    ├── subprocess.run("python cli.py vlm act ...")         → VLM step
    └── subprocess.run("python cli.py device tap ...")      → action execution
"""

import json
import os
import re
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field
from typing import Optional

# Pre-import to avoid import-lock contention with daemon threads.
# device.py transitively imports requests (slow first load with CA certs).
from phonecli.device import get_screen_size, swipe, get_current_app, KNOWN_BUNDLE_IDS, resolve_bundle_id  # noqa: F401


# ---------------------------------------------------------------------------
# Action parser — extracts function calls from LLM/VLM responses
# ---------------------------------------------------------------------------

_ACTION_PATTERNS = [
    # Tagged formats
    r'Action:\s*(.*?)(?=\n|$)',
    r'<CALLED_FUNCTION>\s*(.*?)\s*</CALLED_FUNCTION>',
    # Code block formats
    r'```(?:\w+)?\s*\n(.*?)\n\s*```',
    r'```\s*(.*?)\s*```',
]

_FALLBACK_PATTERNS = [
    r'(tap\([^)]+\))',
    r'(swipe\([^)]+\))',
    r'(text\([^)]+\))',
    r'(long_press\([^)]+\))',
    r'(finish\([^)]*\))',
    r'(wait\([^)]*\))',
    r'(back\(\))',
    r'(home\(\))',
    r'(launch\([^)]+\))',
    r'(macro\(.+?\))',
    r'(type\([^)]+\))',
]


def parse_action(text: str) -> Optional[dict]:
    """Parse an action from a model response.

    Returns a dict like:
        {"name": "tap", "args": [0.5, 0.3]}
        {"name": "text", "args": ["hello"]}
        {"name": "finish", "args": ["task done"]}
        {"name": "back", "args": []}
    """
    if not text:
        return None

    # Try structured patterns first
    for pattern in _ACTION_PATTERNS:
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            code = match.group(1).strip()
            if code:
                return _parse_call(code)

    # Fallback: find any function-like pattern
    for pattern in _FALLBACK_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return _parse_call(match.group(1))

    return None


def _parse_call(code: str) -> Optional[dict]:
    """Parse a single function call like 'tap(0.5, 0.3)' or 'type("hello")'."""
    code = code.strip()

    # Match function name and everything between first ( and last )
    m = re.match(r'(\w+)\s*\((.*)\)\s*$', code)
    if not m:
        return None

    name = m.group(1).lower()
    args_str = m.group(2).strip()

    if not args_str:
        return {"name": name, "args": []}

    # Parse arguments — handle quoted strings and numbers
    args = []
    i = 0
    while i < len(args_str):
        # Skip whitespace and commas
        while i < len(args_str) and args_str[i] in " ,":
            i += 1
        if i >= len(args_str):
            break

        if args_str[i] == '"' or args_str[i] == "'":
            # Quoted string — build unescaped result
            quote = args_str[i]
            i += 1
            buf = []
            while i < len(args_str) and args_str[i] != quote:
                if args_str[i] == "\\" and i + 1 < len(args_str):
                    i += 1  # skip backslash, take next char literally
                buf.append(args_str[i])
                i += 1
            args.append("".join(buf))
            i += 1  # skip closing quote
        else:
            # Number or bare word
            start = i
            while i < len(args_str) and args_str[i] not in " ,)":
                i += 1
            token = args_str[start:i].strip()
            if not token:
                continue
            try:
                if "." in token:
                    args.append(float(token))
                else:
                    args.append(int(token))
            except ValueError:
                args.append(token)

    return {"name": name, "args": args}


# ---------------------------------------------------------------------------
# CLI runner — subprocess wrapper
# ---------------------------------------------------------------------------

def _cli_path() -> str:
    """Get the path to cli.py."""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "cli.py")


def _run_cli(*args, timeout: int = 60) -> dict:
    """Run a CLI subcommand and return parsed JSON result."""
    cmd = [sys.executable, _cli_path()] + list(args)
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if r.returncode != 0:
            return {"status": "error", "message": f"CLI exited {r.returncode}: {r.stderr[:200]}"}
        return json.loads(r.stdout.strip())
    except subprocess.TimeoutExpired:
        return {"status": "error", "message": "CLI timeout"}
    except json.JSONDecodeError as e:
        return {"status": "error", "message": f"JSON parse error: {e}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

@dataclass
class AgentConfig:
    llm_api_key: str = "EMPTY"
    llm_api_base: str = "http://localhost:8002/v1"
    llm_model: str = "Qwen/Qwen2.5-3B-Instruct"
    vlm_api_key: str = "EMPTY"
    vlm_api_base: str = "http://localhost:8002/v1"
    vlm_model: str = "Qwen/Qwen2.5-3B-Instruct"
    max_rounds: int = 25
    request_interval: float = 3.0
    wda_url: str = "http://localhost:8100"
    task_dir: str = "./phonecli_logs"
    enable_xml_verify: bool = False

    @classmethod
    def from_env(cls) -> "AgentConfig":
        return cls(
            llm_api_key=os.getenv("PHONECLI_LLM_API_KEY", os.getenv("API_KEY", "EMPTY")),
            llm_api_base=os.getenv("PHONECLI_LLM_API_BASE", os.getenv("API_BASE", "http://localhost:8002/v1")),
            llm_model=os.getenv("PHONECLI_LLM_MODEL", os.getenv("MODEL_NAME", "Qwen/Qwen2.5-3B-Instruct")),
            vlm_api_key=os.getenv("PHONECLI_VLM_API_KEY", os.getenv("API_KEY", "EMPTY")),
            vlm_api_base=os.getenv("PHONECLI_VLM_API_BASE", os.getenv("API_BASE", "http://localhost:8002/v1")),
            vlm_model=os.getenv("PHONECLI_VLM_MODEL", os.getenv("MODEL_NAME", "Qwen/Qwen2.5-3B-Instruct")),
            wda_url=os.getenv("PHONECLI_WDA_URL", "http://localhost:8100"),
            task_dir=os.getenv("PHONECLI_TASK_DIR", "./phonecli_logs"),
            enable_xml_verify=os.getenv("PHONECLI_ENABLE_XML_VERIFY", "").lower() in ("true", "1", "yes"),
        )


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

@dataclass
class AgentState:
    """Mutable state tracked across rounds."""
    round: int = 0
    history: list[str] = field(default_factory=list)
    macro_played: bool = False
    vlm_steps: int = 0
    screen_w: int = 390
    screen_h: int = 844
    current_screenshot: str = ""
    current_screen: str = ""  # identified screen_id from app map
    bundle_id: str = ""
    app_name: str = ""
    is_done: bool = False
    used_op_id: str = ""  # operation ID used (for memory recording)


class PhoneAgent:
    """Orchestrates task execution via CLI subprocess calls.

    Flow:
        Round 1:  LLM map-task → macro replay → VLM takeover/verify
        Round 2+: VLM act → device execute → repeat
    """

    def __init__(self, config: AgentConfig = None):
        self.config = config or AgentConfig.from_env()
        self.state = AgentState()
        self._session_id = None  # cached WDA session
        self._keepalive_stop = None  # background keepalive thread
        self._app_maps: dict = {}  # app_name → AppMap (multi-map support)
        self._memory_hints = ""  # memory context injected by daemon
        self._in_plan = False  # guard against recursive planner calls
        self._vlm_fail_streak = 0  # consecutive VLM parse failures for escalation

    @property
    def _app_map(self):
        """Backward-compat: first loaded app map."""
        return next(iter(self._app_maps.values()), None) if self._app_maps else None

    def reset_state(self):
        """Clear agent state for re-entrant task execution (used by daemon mode)."""
        self.state = AgentState()
        self._app_maps = {}
        self._memory_hints = ""
        self._vlm_fail_streak = 0
        self._in_plan = False

    def _ensure_session(self):
        """Create a WDA session once and reuse it across all CLI calls."""
        if self._session_id:
            return
        from phonecli.device import create_session, is_wda_ready
        if not is_wda_ready(self.config.wda_url):
            print("[Agent] Warning: WDA not ready, session creation may fail")
            return
        ok, sid = create_session(self.config.wda_url)
        if ok:
            self._session_id = sid
            print(f"[Agent] WDA session created: {sid[:20]}...")
        else:
            print(f"[Agent] Warning: could not create WDA session: {sid}")

    def _wda_tags(self) -> list:
        """Return WDA-related CLI args positioned BEFORE the subcommand.

        Click requires top-level options (--wda-url, --session-id) to appear
        before the subcommand group name.
        """
        tags = ["--wda-url", self.config.wda_url]
        if self._session_id:
            tags.extend(["--session-id", self._session_id])
        return tags

    def _start_keepalive(self, interval: int = 25):
        """Start a background thread that keeps the device screen awake."""
        if not self._session_id:
            return
        wda_url = self.config.wda_url
        session_id = self._session_id
        stopped = threading.Event()

        def _loop():
            import requests
            base = wda_url.rstrip("/")
            # Primary: disable idle timer (no actions needed)
            try:
                r = requests.post(f"{base}/wda/settings",
                                  json={"settings": {"idleTimerDisabled": True}},
                                  timeout=5)
                if r.status_code in (200, 201):
                    print("[Keepalive] idleTimerDisabled: ON")
                    while not stopped.wait(interval * 2):
                        try:
                            requests.get(f"{base}/status", timeout=5)
                        except Exception:
                            pass
                    return
            except Exception:
                pass
            # Fallback: safe status-bar swipe
            from phonecli.device import get_screen_size, swipe
            for retry in range(5):
                try:
                    w, h = get_screen_size(wda_url, session_id)
                    sy = max(h // 40, 5)
                    print(f"[Keepalive] Safe swipe every {interval}s (status bar)")
                    while not stopped.wait(interval):
                        try:
                            swipe(5, sy, 15, sy, duration_ms=100,
                                  wda_url=wda_url, session_id=session_id)
                        except Exception:
                            pass
                    return
                except Exception:
                    if retry < 4:
                        stopped.wait(5)  # wait before retry
            # All retries exhausted, keepalive fallback disabled

        t = threading.Thread(target=_loop, daemon=True)
        t.start()
        self._keepalive_stop = stopped

    def _stop_keepalive(self):
        if self._keepalive_stop:
            self._keepalive_stop.set()
            self._keepalive_stop = None

    def _with_wda(self, *args: str) -> list:
        """Insert WDA tags before the subcommand group for correct Click parsing.

        e.g. _with_wda("device", "screenshot", "--output", path)
          → ["--wda-url", url, "--session-id", sid, "device", "screenshot", "--output", path]
        """
        return self._wda_tags() + list(args)

    def run(self, task: str, app_map_paths: list = None) -> dict:
        """Run a task end-to-end. Returns final result dict.

        Manages WDA session and keepalive lifecycle.
        For daemon mode, use run_task() instead.

        Args:
            task: Task description.
            app_map_paths: List of app map YAML paths (None = pure VLM).
        """
        self._ensure_session()
        self._start_keepalive()
        try:
            return self.run_task(task, app_map_paths)
        finally:
            self._stop_keepalive()

    def run_task(self, task: str, app_map_paths: list = None,
                 memory=None, suggested_op: str = None) -> dict:
        """Execute a single task reusing an existing WDA session.

        Does NOT manage session or keepalive — caller is responsible.
        Used by daemon mode for re-entrant task execution.

        Args:
            task: Task description.
            app_map_paths: List of app map YAML paths (None = pure VLM).
            memory: Optional DialogueMemory for context injection.
            suggested_op: Optional operation ID from memory (bypasses LLM map-task).
        """
        self._setup(task, app_map_paths, memory=memory)

        if self._app_maps:
            self._round_macro(task, memory=memory, suggested_op=suggested_op)

        while self.state.round < self.config.max_rounds:
            if self.state.is_done:
                break
            self.state.round += 1
            self._round_vlm(task, memory=memory)

        return {
            "status": "completed" if self.state.is_done else "max_rounds",
            "task": task,
            "rounds": self.state.round,
            "vlm_steps": self.state.vlm_steps,
            "history": self.state.history[-10:],
        }

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def _setup(self, task: str, app_map_paths: list = None, memory=None):
        os.makedirs(self.config.task_dir, exist_ok=True)

        # Load all app maps
        if app_map_paths:
            from phonecli.app_map import AppMap
            screen_set = False
            for path in app_map_paths:
                if not os.path.exists(path):
                    continue
                am = AppMap(path)
                self._app_maps[am.app_name] = am
                # Use first map's screen dimensions
                if not screen_set:
                    self.state.screen_w = am.screen_w
                    self.state.screen_h = am.screen_h
                    if not self.state.app_name:
                        self.state.app_name = am.app_name
                        self.state.bundle_id = am.package
                    screen_set = True

            if not self._app_maps:
                self._detect_screen_size()
        else:
            self._detect_screen_size()

        # Inject memory hints if available (daemon mode).
        # Use the first app map for hint scoping; multi-map hints are pre-set by daemon.
        first_map = self._app_map
        if memory and hasattr(memory, 'get_hints') and first_map:
            session_hints = memory.get_hints(first_map.app_name, task)
            if session_hints:
                if self._memory_hints:
                    self._memory_hints = self._memory_hints + "\n\n" + session_hints
                else:
                    self._memory_hints = session_hints

        print(f"[Agent] Task: {task}")
        if self._app_maps:
            maps_str = ", ".join(self._app_maps.keys())
            print(f"[Agent] App maps: {maps_str}")
        print(f"[Agent] Screen: {self.state.screen_w}x{self.state.screen_h}")

    def _detect_screen_size(self):
        """Detect screen dimensions from WDA."""
        info_args = self._with_wda("device", "info")
        result = _run_cli(*info_args)
        if result.get("status") == "ok":
            w = result.get("width")
            h = result.get("height")
            if w and h:
                self.state.screen_w = w
                self.state.screen_h = h

    def _get_screenshot_path(self, round_num: int = None) -> str:
        r = round_num if round_num is not None else self.state.round
        return os.path.join(self.config.task_dir, f"screenshot_{r}.png")

    def _get_xml_path(self, round_num: int = None) -> str:
        r = round_num if round_num is not None else self.state.round
        return os.path.join(self.config.task_dir, f"dump_{r}.xml")

    # ------------------------------------------------------------------
    # Round 1: macro routing
    # ------------------------------------------------------------------

    def _round_macro(self, task: str, memory=None,
                     suggested_op: str = None, target_app: str = None):
        """Round 1: map task to operation via LLM, then replay macro.

        With multiple app maps loaded, tries each map's LLM map-task
        sequentially until an operation is found.
        If target_app is set, that app's map is tried first.
        """
        self.state.round = 1
        if not self._app_maps:
            self._prepare_vlm("No app maps loaded.")
            return

        op_info = None  # (op_id, op_type, is_combo, op_desc, app_map)

        # Step 0: If memory suggested an operation, find which map owns it
        if suggested_op:
            for am in self._app_maps.values():
                ops = am.build_operations()
                if suggested_op in ops:
                    op = ops[suggested_op]
                    op_info = (suggested_op, op.type, False, op.description, am)
                    print(f"[Agent] Memory suggested OP: {suggested_op} "
                          f"[{am.app_name}] — bypassing LLM")
                    break

        # Step 1: Try each app map's LLM map-task until an op is found
        if op_info is None:
            # Sort maps: target_app first, then task-mentioned, then rest
            task_lower = task.lower()
            target_lower = target_app.lower() if target_app else ""
            sorted_maps = sorted(
                self._app_maps.values(),
                key=lambda am: (
                    0 if am.app_name.lower() == target_lower else
                    1 if am.app_name.lower() in task_lower else
                    2
                ),
            )

            # Build list of maps to try; skip if target_app has no loaded map
            maps_to_try = sorted_maps
            if target_app:
                target_has_map = any(
                    am.app_name.lower() == target_lower
                    for am in self._app_maps.values()
                )
                if not target_has_map:
                    print(f"[Agent] Target app [{target_app}] has no loaded map — "
                          f"skipping LLM mapping, falling back to VLM")
                    maps_to_try = []

            for am in maps_to_try:
                print(f"[Agent] Round 1: mapping task via {am.app_name} map...")
                llm_args = [
                    "llm", "map-task",
                    "--app-map", am.map_path,
                    "--task", task,
                    "--api-key", self.config.llm_api_key,
                    "--api-base", self.config.llm_api_base,
                    "--model", self.config.llm_model,
                ]
                if self._memory_hints:
                    llm_args.extend(["--memory-hints", self._memory_hints])
                result = _run_cli(*llm_args)

                if result.get("status") != "ok":
                    print(f"[Agent] {am.app_name} map-task failed: "
                          f"{result.get('message')}")
                    continue

                rtype = result.get("result")

                if rtype == "finish":
                    print(f"[Agent] Task answerable via {am.app_name}: "
                          f"{result.get('answer')}")
                    self.state.is_done = True
                    self.state.history.append(f"FINISH: {result.get('answer')}")
                    return

                elif rtype == "op_found":
                    op_info = (
                        result["op_id"],
                        result["type"],
                        result.get("is_macro_vlm", False),
                        result["description"],
                        am,
                    )
                    break

                elif rtype == "need_vlm":
                    print(f"[Agent] {am.app_name}: NEED_VLM — "
                          f"{result.get('reason')}")
                    continue

                elif rtype == "op_not_found":
                    similar = result.get("similar", [])
                    print(f"[Agent] {am.app_name}: OP not found. "
                          f"Similar: {similar}")
                    continue

                else:
                    print(f"[Agent] {am.app_name}: unrecognized response "
                          f"({rtype}), trying next map")
                    continue

            # If no map matched, try task decomposition via Planner
            if op_info is None:
                if not self._in_plan:
                    print("[Agent] No app map matched — trying task planner...")
                    plan = self._try_decompose(task)
                    if plan and len(plan) > 1:
                        self._execute_plan(plan, memory=memory)
                        return

                # Already in plan, Planner failed, or single-step — fall back to VLM
                print("[Agent] Falling back to pure VLM")
                task_lower = task.lower()
                candidate_bid = None

                # Priority 1: target_app (from plan execution)
                if target_app:
                    candidate_bid = resolve_bundle_id(target_app)
                    if candidate_bid:
                        self.state.app_name = target_app
                        self.state.bundle_id = candidate_bid

                # Priority 2: task mentions a loaded map's app
                if not candidate_bid:
                    for am in sorted(self._app_maps.values(),
                                     key=lambda m: 0 if m.app_name.lower() in task_lower else 1):
                        if am.app_name.lower() in task_lower:
                            self.state.app_name = am.app_name
                            self.state.bundle_id = am.package
                            candidate_bid = am.package
                            break

                # Priority 3: task mentions a known app name
                if not candidate_bid:
                    for app_name in KNOWN_BUNDLE_IDS:
                        if app_name.lower() in task_lower:
                            candidate_bid = KNOWN_BUNDLE_IDS[app_name]
                            self.state.app_name = app_name
                            self.state.bundle_id = candidate_bid
                            break

                self._prepare_vlm("No matching operation in any app map.")
                return

        # Auto-upgrade to MACRO_VLM when task requires content interaction
        # and LLM returned a terminal OP instead of MACRO_VLM.
        # Example: "搜索蓝牙耳机" matched "首页→搜索→销量" but the macro
        # only navigates — VLM must type the query and read results.
        _INPUT_HINTS = ["搜索", "查找", "输入", "search", "find", "type",
                        "写", "记录", "记", "录入", "填写"]
        _task_needs_input = any(kw in task.lower() for kw in _INPUT_HINTS)
        if op_info and _task_needs_input and op_info[1] not in ("NAV",) and not op_info[2]:
            print(f"[Agent] Task needs content input — upgrading OP to MACRO_VLM")
            op_info = (op_info[0], op_info[1], True, op_info[3], op_info[4])

        # Step 2: Replay macro
        op_id, op_type, is_combo, op_desc, am = op_info
        self.state.used_op_id = op_id
        self.state.app_name = am.app_name
        self.state.bundle_id = am.package
        macro_args = self._with_wda(
            "macro", "run",
            "--app-map", am.map_path,
            "--op-id", op_id,
        )
        mr = _run_cli(*macro_args)
        if mr.get("status") != "ok":
            print(f"[Agent] Macro replay failed: {mr.get('message')}")
            self._prepare_vlm("Macro replay failed. Starting from current screen.")
            return

        print(f"[Agent] Macro replayed [{am.app_name}]: {op_desc}")

        if op_type == "NAV" or is_combo:
            self._prepare_vlm(f"Macro navigated to: {op_desc}", launch=False)
            print("[Agent] Macro done, VLM takeover...")
        else:
            self.state.macro_played = True
            self.state.history.append(
                f"Macro executed [{am.app_name}]: {op_desc}. Verify completion."
            )
            print("[Agent] Macro executed, VLM verification...")
            verify_path = self._get_screenshot_path(1)
            self._screenshot(verify_path)
            vlm_args = [
                "vlm", "verify",
                "--task", task,
                "--screenshot", verify_path,
                "--api-key", self.config.vlm_api_key,
                "--api-base", self.config.vlm_api_base,
                "--model", self.config.vlm_model,
            ]
            vr = _run_cli(*vlm_args)
            if vr.get("result") == "complete":
                print(f"[Agent] Verified complete: {vr.get('message')}")
                self.state.is_done = True
            else:
                print(f"[Agent] Not yet complete: {vr.get('reason', 'unknown')}")
                self._prepare_vlm(
                    f"Macro replay incomplete ({vr.get('reason', 'unknown')}), "
                    "VLM takeover.", launch=False)

    def _prepare_vlm(self, reason: str = "", launch: bool = True):
        """Prepare for VLM takeover. Set history, optionally launch app."""
        self.state.macro_played = True
        if launch and self.state.bundle_id:
            print(f"[Agent] Launching app: {self.state.bundle_id}")
            launch_args = self._with_wda("device", "launch", self.state.bundle_id)
            _run_cli(*launch_args)
            time.sleep(2)
        msg = reason or "Starting VLM from current screen."
        self.state.history.append(msg)
        print(f"[Agent] {msg}")

    def _vlm_escalate_if_stuck(self, task: str):
        """If VLM has failed to produce valid actions 3+ times in a row,
        inject a back() or home() to break the loop before loop detection fires."""
        if self._vlm_fail_streak < 3:
            return
        print(f"[Agent] VLM stuck ({self._vlm_fail_streak} consecutive parse failures) — "
              f"injecting home() to break out")
        # Reset fail streak
        self._vlm_fail_streak = 0
        # Inject a home + brief pause to reset context
        _run_cli(*self._with_wda("device", "home"))
        time.sleep(1.5)
        self.state.history.append("ESCALATE: home() — VLM stuck, resetting context")

    # ------------------------------------------------------------------
    # Task decomposition (Planner)
    # ------------------------------------------------------------------

    def _try_decompose(self, task: str) -> list:
        """Try to decompose a complex multi-app task via the CLI planner.

        Returns a list of subtask dicts, or empty list on failure.
        """
        if len(self._app_maps) < 1:
            return []
        if self._in_plan:
            return []  # already inside plan execution, don't recurse

        plan_args = [
            "llm", "plan",
            "--task", task,
            "--api-key", self.config.llm_api_key,
            "--api-base", self.config.llm_api_base,
            "--model", self.config.llm_model,
        ]
        for am in self._app_maps.values():
            plan_args.extend(["--app-map", am.map_path])
        if self._memory_hints:
            plan_args.extend(["--memory-hints", self._memory_hints])

        result = _run_cli(*plan_args)
        if result.get("status") != "ok" or result.get("steps", 0) <= 1:
            return []

        plan = result.get("plan", [])
        print(f"[Agent] Planner: {len(plan)} subtasks")
        for s in plan:
            print(f"  {s.get('step', '?')}. [{s.get('app', '?')}] {s.get('subtask', '?')}")
        return plan

    def _execute_plan(self, plan: list, memory=None):
        """Execute a decomposed plan: macro for each subtask, then VLM if needed."""
        self._in_plan = True
        base_dir = self.config.task_dir
        try:
            for step in plan:
                sub_task = step.get("subtask", "")
                app_name = step.get("app", "")
                step_no = step.get("step", len(plan))
                print(f"\n[Agent] === Step {step_no}/{len(plan)}: [{app_name}] {sub_task} ===")

                # Isolate per-step screenshots and reset per-step state
                self.config.task_dir = os.path.join(base_dir, f"step_{step_no}")
                self.state.macro_played = False
                self.state.is_done = False
                self.state.round = 0
                self._vlm_fail_streak = 0
                self.state.history.clear()
                self.state.history.append(f"--- Step {step_no}: [{app_name}] {sub_task} ---")

                # Try macro routing for this subtask (prioritize target app's map)
                self._round_macro(sub_task, memory=memory, target_app=app_name)

                # If macro didn't complete, continue with VLM
                while (not self.state.is_done
                       and self.state.round < self.config.max_rounds):
                    self.state.round += 1
                    self._round_vlm(sub_task, memory=memory)

            self.state.is_done = True
        finally:
            self.config.task_dir = base_dir
            self._in_plan = False

    # ------------------------------------------------------------------
    # Round 2+: VLM loop
    # ------------------------------------------------------------------

    def _round_vlm(self, task: str, memory=None):
        if self.state.is_done:
            return

        # Dump XML once — shared between verification and screen identification
        xml_path = self._get_xml_path()
        self._screenshot_xml(xml_path)

        # Optional: XML text verification
        if self.config.enable_xml_verify:
            vr = _run_cli(
                "llm", "xml-verify",
                "--task", task,
                "--xml-file", xml_path,
                "--api-key", self.config.llm_api_key,
                "--api-base", self.config.llm_api_base,
                "--model", self.config.llm_model,
            )
            if vr.get("result") == "finish":
                print(f"[Agent] XML verify: task complete — {vr.get('answer')}")
                self.state.is_done = True
                self.state.history.append(f"XML FINISH: {vr.get('answer')}")
                return

        # Screenshot
        ss_path = self._get_screenshot_path()
        self._screenshot(ss_path)
        self.state.current_screenshot = ss_path

        # Detect current foreground app via WDA first (before screen identification)
        cur_app_name = self.state.app_name
        cur_bundle = self.state.bundle_id
        try:
            cur_bundle = get_current_app(self.config.wda_url, self._session_id)
            if cur_bundle and cur_bundle != "unknown":
                cur_app_name = cur_bundle
                for am in self._app_maps.values():
                    if cur_bundle == am.package:
                        cur_app_name = am.app_name
                        break
                if cur_bundle == "com.apple.mobilesafari":
                    cur_app_name = "Safari"
                elif cur_bundle == "com.apple.mobilenotes":
                    cur_app_name = "备忘录"
                if cur_bundle != self.state.bundle_id:
                    self.state.bundle_id = cur_bundle
                    self.state.app_name = cur_app_name
                    print(f"[Agent] Foreground app: {cur_app_name} ({cur_bundle})")
        except Exception:
            pass

        # Screen identification via XML — only match map belonging to current foreground app
        screen_hint = ""
        if self._app_maps:
            try:
                with open(xml_path, "r") as f:
                    xml_str = f.read()
                best_sid, best_conf, best_am = None, 0.0, None
                for am in self._app_maps.values():
                    # Only match maps for the current foreground app
                    if cur_bundle and cur_bundle != "unknown" and am.package != cur_bundle:
                        continue
                    sid, confidence = am.identify_current_screen(xml_str)
                    if sid and confidence > best_conf:
                        best_sid, best_conf, best_am = sid, confidence, am

                if best_sid and best_conf >= 0.5:
                    self.state.current_screen = best_sid

                    # Build rich screen hint with description, nav targets, scroll info
                    enriched = best_am.build_enriched_screen_hint(best_sid)
                    if enriched:
                        enriched += "\n\n"
                    screen_hint = enriched

                    targets = best_am.get_nav_targets(best_sid)
                    print(f"[Agent] Screen [{best_am.app_name}]: {best_sid} "
                          f"({best_conf:.0%}), nav: {targets}")
            except Exception:
                pass

        # Loop detection — compare by action type, not exact coords
        if len(self.state.history) >= 3:
            _KNOWN_ACTIONS = {"tap", "swipe", "type", "text", "back", "home",
                             "launch", "macro", "wait", "long_press"}
            recent = [h for h in self.state.history[-6:]
                      if h and h.split("(")[0].split("→")[0].strip() in _KNOWN_ACTIONS]
            if len(recent) >= 3:
                actions = [h.split("(")[0].split("→")[0].strip() for h in recent[-3:]]
                if len(set(actions)) == 1:
                    print(f"[Agent] Loop detected ({actions[0]} x3) — aborting VLM")
                    self.state.is_done = True
                    self.state.history.append(
                        f"LOOP_ABORT: Repeated {actions[0]} 3 times with no progress."
                    )
                    return

        # Build history context (include screen identification + current app + available apps)
        # Available apps for launch()
        _avail = [f"{am.app_name} ({am.package})" for am in self._app_maps.values()]
        for _an, _bid in KNOWN_BUNDLE_IDS.items():
            _entry = f"{_an} ({_bid})"
            if _entry not in _avail:
                _avail.append(_entry)
        _avail_list = "\n".join(f"  - {a}" for a in sorted(_avail))
        history_context = (
            f"## Current App\nYou are currently in: {cur_app_name} "
            f"({self.state.bundle_id})\n\n"
            f"## Available Apps (use launch(name) to switch)\n{_avail_list}\n\n"
        )
        history_context += screen_hint
        if self.state.history:
            recent = self.state.history[-5:]
            history_context += "Previous observations:\n" + "\n".join(
                f"  {h}" for h in recent
            ) + "\n\n"

        # Inject memory hints if available (daemon mode).
        # Use the currently identified app, falling back to first map.
        current_app = self.state.app_name or (
            next(iter(self._app_maps)) if self._app_maps else ""
        )
        if memory and hasattr(memory, 'get_hints') and current_app:
            hints = memory.get_hints(current_app, task)
            if hints:
                history_context += "\n## Past experience in this session\n" + hints + "\n"

        # Call VLM
        self.state.vlm_steps += 1
        print(f"[Agent] VLM step {self.state.vlm_steps}...")
        vlm_args = [
            "vlm", "act",
            "--task", task,
            "--screenshot", ss_path,
            "--history", history_context,
            "--api-key", self.config.vlm_api_key,
            "--api-base", self.config.vlm_api_base,
            "--model", self.config.vlm_model,
        ]
        result = _run_cli(*vlm_args)

        if result.get("status") != "ok":
            print(f"[Agent] VLM error: {result.get('message')}")
            self.state.history.append(f"[error: {result.get('message', 'VLM failed')[:100]}]")
            self._vlm_fail_streak += 1
            self._vlm_escalate_if_stuck(task)
            return

        action = result.get("action")
        if not action:
            print(f"[Agent] No action parsed")
            self._vlm_fail_streak += 1
            self._vlm_escalate_if_stuck(task)
            return

        # VLM produced a valid action — reset fail streak
        self._vlm_fail_streak = 0

        # Extract state assessment from raw response
        raw = result.get("raw_response", "")
        state_match = re.search(r'State Assessment:\s*(.*?)(?=\s*\bAction:|\Z)',
                                raw, re.DOTALL | re.IGNORECASE)
        if state_match:
            self.state.history.append(state_match.group(1).strip())

        # Execute action via device CLI
        pre_action_ss = self.state.current_screenshot
        self._execute_action(action)

        # Action feedback: check if action had visible effect
        if os.path.exists(pre_action_ss):
            post_action_ss = self._get_screenshot_path(
                self.state.round + 1000  # unique temp path
            )
            self._screenshot(post_action_ss)
            if os.path.exists(post_action_ss):
                changed = self._image_diff_pct(pre_action_ss, post_action_ss)
                if changed < 0.01:
                    print(f"[Agent] Action had NO visible effect ({changed:.1%})")
                    self.state.history.append(
                        "WARNING: Previous action had NO visible effect — "
                        "screen unchanged. Try different coordinates or approach."
                    )
                    try:
                        os.remove(post_action_ss)
                    except Exception:
                        pass
                else:
                    # Replace pre-action screenshot for next round comparison
                    try:
                        os.replace(post_action_ss, pre_action_ss)
                    except Exception:
                        pass

    # ------------------------------------------------------------------
    # Action execution
    # ------------------------------------------------------------------

    def _execute_action(self, action: dict):
        name = action["name"]
        args = action.get("args", [])

        if name == "finish":
            msg = args[0] if args else "Task complete"
            print(f"[Agent] FINISH: {msg}")
            self.state.is_done = True
            self.state.history.append(f"FINISH: {msg}")
            return

        elif name == "tap":
            if len(args) >= 2:
                x, y = self._to_point(args[0], args[1])
                print(f"[Agent] tap({args[0]:.3f}, {args[1]:.3f}) → ({x}, {y})")
                _run_cli(*self._with_wda("device", "tap", str(x), str(y)))
                self.state.history.append(f"tap({x},{y})")

        elif name == "long_press":
            if len(args) >= 2:
                x, y = self._to_point(args[0], args[1])
                print(f"[Agent] long_press({args[0]:.3f}, {args[1]:.3f})")
                _run_cli(*self._with_wda("device", "long-press", str(x), str(y)))
                self.state.history.append(f"long_press({x},{y})")

        elif name == "swipe":
            if len(args) == 1:
                direction = str(args[0]).strip('"').strip("'").lower()
                if direction in ("up", "down", "left", "right"):
                    x1, y1, x2, y2 = self._swipe_coords(direction)
                else:
                    print(f"[Agent] Unknown swipe direction '{direction}', "
                          f"defaulting to down")
                    x1, y1, x2, y2 = self._swipe_coords("down")
            elif len(args) >= 4:
                x1, y1 = self._to_point(args[0], args[1])
                x2, y2 = self._to_point(args[2], args[3])
            else:
                return
            print(f"[Agent] swipe({x1},{y1}) → ({x2},{y2})")
            _run_cli(*self._with_wda("device", "swipe",
                                     str(x1), str(y1), str(x2), str(y2)))
            self.state.history.append(f"swipe({x1},{y1}→{x2},{y2})")

        elif name in ("type", "text"):
            if args:
                t = str(args[0])
                print(f"[Agent] type: {t[:40]}")
                _run_cli(*self._with_wda("device", "text", t))
                self.state.history.append(f"type({t[:30]})")

        elif name == "back":
            print("[Agent] back()")
            _run_cli(*self._with_wda("device", "back"))
            self.state.history.append("back()")

        elif name == "home":
            print("[Agent] home()")
            _run_cli(*self._with_wda("device", "home"))
            self.state.history.append("home()")

        elif name == "launch":
            app = str(args[0]).strip('"').strip("'") if args else self.state.bundle_id
            # Resolve app name to bundle ID: loaded maps → known bundle IDs
            bid = app
            for am in self._app_maps.values():
                if app.lower() == am.app_name.lower() or app == am.package:
                    bid = am.package
                    break
            if bid == app:
                resolved = resolve_bundle_id(app)
                if resolved:
                    bid = resolved
            print(f"[Agent] launch({app}) → {bid}")
            _run_cli(*self._with_wda("device", "launch", bid))
            self.state.history.append(f"launch({app})")
            # Update state to reflect the new app
            for am in self._app_maps.values():
                if bid == am.package:
                    self.state.app_name = am.app_name
                    self.state.bundle_id = bid
                    self.state.current_screen = "screen_0"
                    break

        elif name == "macro":
            target = str(args[0]).strip('"').strip("'") if args else ""
            print(f"[Agent] macro({target})")
            if not self._app_maps or not self.state.current_screen:
                self.state.history.append(
                    f"macro({target}) failed: no app maps or unknown current screen"
                )
                return
            from_id = self.state.current_screen

            # Find which app map owns the current screen.
            # Prefer the current app's map to avoid cross-map collisions
            # (e.g. screen_3 exists in multiple maps).
            owner_map = None
            current_app = self.state.app_name
            if current_app and current_app in self._app_maps:
                am = self._app_maps[current_app]
                if am.get_screen(from_id):
                    owner_map = am
            if not owner_map:
                for am in self._app_maps.values():
                    if am.get_screen(from_id):
                        owner_map = am
                        break

            if not owner_map:
                self.state.history.append(
                    f"macro({target}) failed: screen {from_id} not found in any map"
                )
                return

            # Find the target screen by element text or alias.
            # Requires ``leads_to`` (navigable during crawl), not ``fixed``.
            from_screen = owner_map.get_screen(from_id)
            to_id = None
            if from_screen:
                target_lower = target.lower()
                for e in from_screen.elements:
                    if not e.leads_to:
                        continue
                    # Match against text or any alias
                    texts = [e.text.lower()] + [a.lower() for a in e.aliases]
                    if target_lower in texts:
                        to_id = e.leads_to
                        break
            if not to_id:
                # Not a nav target — try fixed elements for direct tap (e.g. search box)
                direct_elem = None
                if from_screen:
                    target_lower = target.lower()
                    for e in from_screen.elements:
                        if not e.fixed:
                            continue
                        texts = [e.text.lower()] + [a.lower() for a in e.aliases]
                        if target_lower in texts:
                            direct_elem = e
                            break
                if direct_elem:
                    x = round(direct_elem.center[0] * owner_map.screen_w)
                    y = round(direct_elem.center[1] * owner_map.screen_h)
                    print(f"[Agent] macro({target}) → direct tap fixed element at ({x}, {y})")
                    _run_cli(*self._with_wda("device", "tap", str(x), str(y)))
                    time.sleep(1.0)
                    self.state.history.append(
                        f"macro({target}) [{owner_map.app_name}]: "
                        f"direct tap at ({x},{y})"
                    )
                    return
                self.state.history.append(
                    f"macro({target}) failed: not a nav or fixed target from {from_id}"
                )
                return
            steps = owner_map.find_relative_macro(from_id, to_id)
            if not steps:
                self.state.history.append(
                    f"macro({target}) failed: no path from {from_id} to {to_id}"
                )
                return
            for step in steps:
                action = step.get("action", "")
                ok = True
                if action == "tap":
                    r = _run_cli(*self._with_wda("device", "tap",
                                                 str(step.get("x", 0)), str(step.get("y", 0))))
                    ok = r.get("status") == "ok"
                elif action == "swipe":
                    r = _run_cli(*self._with_wda("device", "swipe",
                                                 str(step.get("x1", 0)), str(step.get("y1", 0)),
                                                 str(step.get("x2", 0)), str(step.get("y2", 0))))
                    ok = r.get("status") == "ok"
                if "wait" in step:
                    time.sleep(step["wait"])
                if not ok:
                    self.state.history.append(
                        f"macro({target}) step failed: {action}"
                    )
                    return
            self.state.current_screen = to_id
            self.state.history.append(
                f"macro({target}) [{owner_map.app_name}]: "
                f"{from_id}→{to_id} ({len(steps)} steps)"
            )

        elif name == "wait":
            try:
                secs = int(float(args[0])) if args else 1
            except (ValueError, TypeError):
                secs = 1
            secs = max(1, min(secs, 10))
            print(f"[Agent] wait({secs}s)")
            time.sleep(secs)
            self.state.history.append(f"wait({secs})")

        else:
            print(f"[Agent] Unknown action: {name}")
            self.state.history.append(f"[unknown action: {name}]")

        time.sleep(self.config.request_interval)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _image_diff_pct(path_a: str, path_b: str) -> float:
        """Return fraction of pixels that differ between two screenshots.

        Returns 0.0 if images are identical, 1.0 if completely different.
        Images are resized to 200px width for fast comparison.
        """
        try:
            from PIL import Image
            import numpy as np
            with Image.open(path_a) as img_a, Image.open(path_b) as img_b:
                new_w = 200
                new_h = int(new_w * img_a.height / img_a.width)
                a = img_a.resize((new_w, new_h))
                b = img_b.resize((new_w, new_h))
                arr_a = np.array(a, dtype=np.float32)
                arr_b = np.array(b, dtype=np.float32)
                diff = np.abs(arr_a - arr_b).mean() / 255.0
                return float(diff)
        except Exception:
            return 1.0  # assume changed on error

    def _to_point(self, rx, ry) -> tuple:
        """Convert normalized coordinates [0,1] to pixel coordinates."""
        px = int(float(rx) * self.state.screen_w)
        py = int(float(ry) * self.state.screen_h)
        return px, py

    def _swipe_coords(self, direction: str) -> tuple:
        """Get pixel swipe coords for up/down/left/right scroll."""
        w, h = self.state.screen_w, self.state.screen_h
        mid_x, mid_y = w // 2, h // 2
        if direction == "up":
            return mid_x, int(h * 0.7), mid_x, int(h * 0.3)
        elif direction == "down":
            return mid_x, int(h * 0.3), mid_x, int(h * 0.7)
        elif direction == "left":
            return int(w * 0.7), mid_y, int(w * 0.3), mid_y
        else:  # right
            return int(w * 0.3), mid_y, int(w * 0.7), mid_y

    def _screenshot(self, path: str):
        _run_cli(*self._with_wda("device", "screenshot", "--output", path))

    def _screenshot_xml(self, path: str):
        _run_cli(*self._with_wda("device", "xml", "--output", path))
