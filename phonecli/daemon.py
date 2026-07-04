#!/usr/bin/env python3
"""Daemon / interactive REPL mode for phonecli.

Usage (via run.py):
    python run.py --interactive
    python run.py --interactive --app-map settings_map.yaml

Connects to WDA once, then accepts tasks one at a time from the terminal.
The device stays connected and the screen is kept awake throughout.

Commands:
    quit, exit, q   — exit daemon
    memory, profile — show persistent user profile
    forget          — clear this session's dialogue memory
    help            — show available commands
    memory --clear  — reset persistent profile
    (anything else) — treated as a task and executed
"""

from __future__ import annotations

import os
import sys
import time
import traceback
from datetime import datetime
from typing import Optional

from phonecli.agent import PhoneAgent, AgentConfig
from phonecli.memory import DialogueMemory, UserMemory


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

QUIT_COMMANDS = {"quit", "exit", "q"}
MEMORY_COMMANDS = {"memory", "profile", "mem"}
FORGET_COMMANDS = {"forget"}
HELP_COMMANDS = {"help", "?"}

BANNER = "=" * 60

HELP_TEXT = """
Available commands:
  <task description>    Run a phone task (e.g. "Turn on Wi-Fi")
  memory, profile       Show persistent user profile
  forget                Clear session dialogue memory
  memory --clear        Reset persistent profile to empty
  help, ?               Show this help
  quit, exit, q         Exit daemon
"""


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def run_daemon(config: AgentConfig, app_map_paths: list = None):
    """Interactive daemon mode — connect once, run many tasks.

    Args:
        config: Agent configuration (LLM/VLM keys, WDA URL, etc.).
        app_map_paths: Optional list of app map YAML paths for macro routing.
    """
    # --- 1. Connect to device ---
    print(f"\n{BANNER}")
    print("[Daemon] Checking WebDriverAgent connection...")
    from phonecli.device import is_wda_ready
    if not is_wda_ready(config.wda_url):
        print(f"[Daemon] ERROR: WebDriverAgent not ready at {config.wda_url}")
        print("Start WDA on your iOS device first.")
        sys.exit(1)
    print("[Daemon] WebDriverAgent ready.")

    # --- 2. Create agent ---
    agent = PhoneAgent(config)
    agent._ensure_session()
    if not agent._session_id:
        print("[Daemon] ERROR: Could not create WDA session.")
        sys.exit(1)

    # --- 3. Keepalive ---
    agent._start_keepalive(interval=25)
    print("[Daemon] Screen keepalive active.")

    # --- 4. Memory ---
    user_memory = UserMemory()
    user_memory.start_session()
    dialogue_memory = DialogueMemory()

    # --- 5. App map info ---
    app_names = []
    if app_map_paths:
        for path in app_map_paths:
            if os.path.exists(path):
                info = _load_app_info(path)
                name = info.get("app", path)
                app_names.append(name)
                print(f"[Daemon] App map loaded: {name} ({path})")
        if not app_names:
            app_map_paths = None

    # --- 6. Banner ---
    print(f"\n{BANNER}")
    print("[Daemon] Interactive mode — device connected.")
    print(user_memory.session_banner())
    if app_names:
        print(f"[Daemon] App maps active: {', '.join(app_names)}")
    print(f"\n[Daemon] Enter a task and press Enter to run it.")
    print("[Daemon] Commands: 'memory' — profile  |  'forget' — reset session  |  'quit' — exit")
    print(f"{BANNER}\n")

    # --- 7. REPL loop ---
    task_count = 0
    try:
        while True:
            try:
                task_instruction = input("[phonecli] Task> ").strip()
            except EOFError:
                print("\n[Daemon] stdin closed. Exiting.")
                break
            except KeyboardInterrupt:
                print("\n[Daemon] Interrupted. Exiting interactive mode.")
                break

            if not task_instruction:
                continue

            # Special commands
            lower = task_instruction.lower()

            if lower in QUIT_COMMANDS:
                print("[Daemon] Goodbye.")
                break

            if lower in HELP_COMMANDS:
                print(HELP_TEXT)
                continue

            if lower in FORGET_COMMANDS:
                dialogue_memory.clear()
                print("[Daemon] Session dialogue memory cleared.")
                continue

            if lower in MEMORY_COMMANDS:
                user_memory.print_summary()
                continue

            if lower.startswith("memory --clear") or lower.startswith("memory --reset"):
                user_memory.clear()
                dialogue_memory.clear()
                continue

            # --- Execute task ---
            task_count += 1
            print(f"\n[Daemon] --- Task #{task_count} -------------------------------")
            _execute_task(
                agent=agent,
                task=task_instruction,
                app_map_paths=app_map_paths,
                user_memory=user_memory,
                dialogue_memory=dialogue_memory,
            )

    finally:
        # --- 8. Cleanup ---
        agent._stop_keepalive()
        print("\n[Daemon] Session ended.")


# ---------------------------------------------------------------------------
# Task execution
# ---------------------------------------------------------------------------

def _execute_task(
    agent: PhoneAgent,
    task: str,
    app_map_paths: Optional[list],
    user_memory: UserMemory,
    dialogue_memory: DialogueMemory,
):
    """Execute a single task within the daemon session."""

    # Load all app names for memory scoping
    app_names = []
    if app_map_paths:
        for path in app_map_paths:
            if os.path.exists(path):
                info = _load_app_info(path)
                name = info.get("app", "")
                if name:
                    app_names.append(name)
    primary_app = app_names[0] if app_names else ""

    start_time = time.time()

    try:
        # Step 1: Check UserMemory (try each app name)
        for app_name in app_names:
            can_answer, answer = user_memory.query(task, app_name)
            if can_answer and answer:
                print(f"[Memory] Answer found in profile: {answer}")
                user_memory.record_task(
                    task=task, status="completed", final_answer=answer,
                    app_name=app_name, rounds=0,
                    duration_seconds=time.time() - start_time,
                )
                dialogue_memory.record(task, answer, app_name)
                return

        # Step 2: Check DialogueMemory
        cached = dialogue_memory.query(task)
        if cached:
            print(f"[Memory] Answered in this session: {cached}")
            return

        # Step 2.5: Check if a macro operation is known (try each app)
        suggested_op = None
        if app_map_paths:
            for app_name in app_names:
                op_id, desc, score = user_memory.suggest_op(task, app_name)
                if op_id and score >= 0.6:
                    suggested_op = op_id
                    print(f"[Memory] Macro suggestion: {op_id} "
                          f"(score={score:.0%}, \"{desc[:60]}\")")
                    break

        # Step 3: Generate task-specific log directory
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        task_dir = os.path.join(agent.config.task_dir, f"task_{ts}")
        original_dir = agent.config.task_dir
        agent.config.task_dir = task_dir
        try:
            # Step 4: Reset agent state and pre-fill memory hints from UserMemory
            agent.reset_state()
            # Collect hints from all known apps
            hint_parts = []
            for app_name in app_names:
                op_hints = user_memory.get_op_hints(task, app_name)
                if op_hints:
                    hint_parts.append(op_hints)
            profile_ctx = user_memory.get_planner_context()
            if profile_ctx:
                hint_parts.append(profile_ctx)
            combined = "\n\n".join(hint_parts)
            if combined:
                agent._memory_hints = combined

            result = agent.run_task(task, app_map_paths, memory=dialogue_memory,
                                    suggested_op=suggested_op)

            duration = time.time() - start_time
            status = result.get("status", "unknown")
            rounds = result.get("rounds", 0)

            # Step 6: Extract answer from history
            final_answer = _extract_answer(result)

            # Step 7: Get the operation ID and app that was actually used
            op_id = agent.state.used_op_id or suggested_op or ""
            actual_app = agent.state.app_name or primary_app

            # Step 8: Record to memory
            user_memory.record_task(
                task=task, status=status, final_answer=final_answer or "",
                app_name=actual_app, op_id=op_id,
                rounds=rounds, duration_seconds=duration,
            )
            if final_answer and status == "completed":
                dialogue_memory.record(task, final_answer, actual_app, op_id)

            # Step 9: Print result
            print(f"\n[Daemon] Status: {status}  [{actual_app}]  |  "
                  f"Rounds: {rounds}  |  "
                  f"Duration: {duration:.1f}s")
            if final_answer:
                print(f"{BANNER}")
                print(f"[Daemon] ANSWER: {final_answer}")
                print(BANNER)

            # Step 10: Extract insights (async — non-blocking on VLM)
            _maybe_extract_insights(user_memory, task, final_answer, agent)
        finally:
            # Always restore original task dir
            agent.config.task_dir = original_dir

    except KeyboardInterrupt:
        print("\n[Daemon] Task interrupted. Ready for next task.")
    except Exception as exc:
        traceback.print_exc()
        print(f"\n[Daemon] Task failed: {exc}")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_app_info(app_map_path: str) -> dict:
    """Load app name and package from a YAML app map."""
    import yaml
    try:
        with open(app_map_path, "r") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


def _extract_answer(result: dict) -> str:
    """Extract a human-readable answer from the agent result."""
    history = result.get("history", [])
    for entry in reversed(history):
        if isinstance(entry, str) and entry.startswith("FINISH:"):
            return entry.replace("FINISH:", "").strip()
    return ""


def _maybe_extract_insights(
    user_memory: UserMemory,
    task: str,
    final_answer: str,
    agent: PhoneAgent,
):
    """Attempt to extract user insights from a completed task.

    Only runs when a VLM agent is available. Failures are silent
    since insight extraction is a best-effort enhancement.
    """
    if not final_answer:
        return
    # Insight extraction requires a VLM agent with an act() method.
    # In the current architecture, the VLM calls go through subprocess,
    # so we skip this for now. Can be wired up when needed.
    pass
