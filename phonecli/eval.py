#!/usr/bin/env python3
"""Task evaluation harness — runs tasks and judges completion via VLM.

Each task: run agent → final screenshot → VLM judge → PASS/FAIL.

Usage:
    python eval.py --app-map settings_map.yaml
    python eval.py --app-map settings_map.yaml --tasks 1,3,5
    python eval.py --no-macro  # pure VLM mode for all tasks
"""

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from phonecli.agent import PhoneAgent, AgentConfig
from phonecli.llm_client import vision_completion

# ---------------------------------------------------------------------------
# Test tasks — (task, success_criteria)
# ---------------------------------------------------------------------------

TASKS = [
    {
        "id": 1,
        "task": "Turn on Airplane Mode",
        "criteria": (
            "Airplane mode icon (a small airplane) should be visible in the "
            "status bar at the top of the screen. The Airplane Mode row in "
            "Settings should show ON or have a green toggle."
        ),
    },
    {
        "id": 2,
        "task": "Open Wi-Fi settings and tell me which network I am connected to",
        "criteria": (
            "The Wi-Fi settings page should be visible (showing 'Wi-Fi' at the "
            "top). A connected network name should be visible with a blue "
            "checkmark next to it, e.g. 'HKU' or similar."
        ),
    },
    {
        "id": 3,
        "task": "Turn off Bluetooth",
        "criteria": (
            "The Bluetooth settings page should be visible. The Bluetooth "
            "toggle should show OFF (no green). The text 'Off' or toggle in "
            "the off position should be visible."
        ),
    },
    {
        "id": 4,
        "task": "Open Battery settings and tell me the battery health percentage",
        "criteria": (
            "The Battery page should be visible (showing 'Battery' at the top). "
            "Battery percentage or 'Battery Health' information should be "
            "displayed on the screen."
        ),
    },
    {
        "id": 5,
        "task": "Go to Settings main page, scroll down, and list at least 10 options you see",
        "criteria": (
            "The Settings main page should be visible with 'Settings' at the top. "
            "Multiple settings rows should be visible (e.g. Airplane Mode, Wi-Fi, "
            "Bluetooth, Cellular, etc.). At least 8-10 options should be listed."
        ),
    },
]

# ---------------------------------------------------------------------------
# VLM judge
# ---------------------------------------------------------------------------

JUDGE_PROMPT = """You are a task completion judge for iOS phone automation. You are given a screenshot and must determine whether the task was completed successfully.

## Task
{task}

## Success Criteria
{criteria}

## Instructions
Look at the screenshot carefully. Output exactly one line:

PASS: <brief reason the task was completed successfully>
FAIL: <brief reason the task failed>

If you can see evidence that the task was completed (e.g. the correct screen is open, the toggle is in the right state, the information is visible), output PASS. Otherwise output FAIL."""


def judge_task(
    task: str,
    criteria: str,
    screenshot_path: str,
    api_key: str = "EMPTY",
    api_base: str = "http://localhost:8002/v1",
    model: str = "Qwen/Qwen2.5-3B-Instruct",
) -> dict:
    """Call VLM to judge whether a task was completed."""
    if not os.path.exists(screenshot_path):
        return {"verdict": "FAIL", "reason": "No screenshot available"}

    prompt = JUDGE_PROMPT.format(task=task, criteria=criteria)
    try:
        rsp = vision_completion(
            prompt, "Judge this screenshot.",
            [screenshot_path],
            api_key=api_key, api_base=api_base, model=model,
            max_tokens=256, temperature=0.0,
        )
    except Exception as e:
        return {"verdict": "ERROR", "reason": f"Judge VLM error: {e}"}

    pass_match = re.search(r'PASS:\s*(.*)', rsp, re.IGNORECASE)
    fail_match = re.search(r'FAIL:\s*(.*)', rsp, re.IGNORECASE)

    if pass_match:
        return {"verdict": "PASS", "reason": pass_match.group(1).strip()}
    elif fail_match:
        return {"verdict": "FAIL", "reason": fail_match.group(1).strip()}
    else:
        return {"verdict": "FAIL", "reason": f"Unrecognized judge response: {rsp[:100]}"}


# ---------------------------------------------------------------------------
# Eval runner
# ---------------------------------------------------------------------------

def run_eval(
    tasks: list[dict],
    app_map_path: Optional[str] = None,
    max_rounds: int = 25,
    request_interval: float = 3.0,
    wda_url: str = "http://localhost:8100",
    task_dir: str = "./phonecli_eval",
    api_key: str = "EMPTY",
    api_base: str = "http://localhost:8002/v1",
    model: str = "Qwen/Qwen2.5-3B-Instruct",
) -> list[dict]:
    """Run all tasks and return results."""
    results = []

    config = AgentConfig.from_env()
    config.max_rounds = max_rounds
    config.request_interval = request_interval
    config.wda_url = wda_url
    config.task_dir = task_dir

    agent = PhoneAgent(config)

    for i, tdef in enumerate(tasks):
        tid = tdef["id"]
        task_text = tdef["task"]
        criteria = tdef["criteria"]
        run_dir = os.path.join(task_dir, f"task_{tid}")
        config.task_dir = run_dir
        agent.reset_state()

        print(f"\n{'='*60}")
        print(f"[Eval] Task {tid}/{len(tasks)}: {task_text}")
        print(f"[Eval] Criteria: {criteria[:80]}...")
        print(f"{'='*60}")

        start = time.time()
        try:
            result = agent.run(task_text, [app_map_path] if app_map_path else None)
        except Exception as e:
            result = {"status": "error", "rounds": 0, "vlm_steps": 0,
                      "history": [str(e)]}
        elapsed = time.time() - start

        # Find the last screenshot
        screenshot_path = ""
        for r in range(result["rounds"], 0, -1):
            p = os.path.join(run_dir, f"screenshot_{r}.png")
            if os.path.exists(p):
                screenshot_path = p
                break

        # Judge
        judge = judge_task(task_text, criteria, screenshot_path,
                           api_key=api_key, api_base=api_base, model=model)

        item = {
            "id": tid,
            "task": task_text,
            "status": result["status"],
            "rounds": result["rounds"],
            "vlm_steps": result["vlm_steps"],
            "elapsed_s": round(elapsed, 1),
            "judge_verdict": judge["verdict"],
            "judge_reason": judge["reason"],
            "final_screenshot": screenshot_path,
        }
        results.append(item)

        print(f"[Eval] Agent: {result['status']} ({result['rounds']}r / {result['vlm_steps']}v)")
        print(f"[Eval] Judge: {judge['verdict']} — {judge['reason'][:100]}")

    return results


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def print_report(results: list[dict]):
    print(f"\n{'='*60}")
    print("EVALUATION REPORT")
    print(f"{'='*60}")
    print(f"{'ID':<4} {'Task':<40} {'Rounds':<7} {'VLM':<5} {'Time':<7} {'Agent':<11} {'Judge':<6}")
    print("-" * 80)

    passes = 0
    for r in results:
        j = r["judge_verdict"]
        if j == "PASS":
            passes += 1
        task_short = r["task"][:38]
        print(f"{r['id']:<4} {task_short:<40} {r['rounds']:<7} {r['vlm_steps']:<5} "
              f"{r['elapsed_s']:<6.0f}s {r['status']:<11} {j:<6}")

    print("-" * 80)
    print(f"Total: {len(results)} tasks | Passed: {passes}/{len(results)} "
          f"| Pass rate: {passes/len(results)*100:.0f}%")

    # Show failed task details
    failed = [r for r in results if r["judge_verdict"] != "PASS"]
    if failed:
        print(f"\nFailed tasks:")
        for r in failed:
            print(f"  Task {r['id']}: {r['judge_verdict']} — {r['judge_reason']}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Phone Agent Evaluation — run tasks and judge completion via VLM",
    )
    parser.add_argument("--app-map", "-m", default=None,
                        help="Path to app map YAML")
    parser.add_argument("--no-macro", action="store_true",
                        help="Pure VLM mode (no app map)")
    parser.add_argument("--tasks", default="1,2,3,4,5",
                        help="Comma-separated task IDs to run (default: all)")
    parser.add_argument("--max-rounds", type=int, default=25)
    parser.add_argument("--request-interval", type=float, default=3.0)
    parser.add_argument("--wda-url", default=None)
    parser.add_argument("--task-dir", default="./phonecli_eval")
    parser.add_argument("--api-key", default=None)
    parser.add_argument("--api-base", default=None)
    parser.add_argument("--model", default=None)
    parser.add_argument("--output", "-o", default=None,
                        help="Save results to JSON")
    args = parser.parse_args()

    # Config
    api_key = args.api_key or os.getenv("PHONECLI_VLM_API_KEY") or os.getenv("API_KEY", "EMPTY")
    api_base = args.api_base or os.getenv("PHONECLI_VLM_API_BASE") or os.getenv("API_BASE", "http://localhost:8002/v1")
    model = args.model or os.getenv("PHONECLI_VLM_MODEL") or os.getenv("MODEL_NAME", "Qwen/Qwen2.5-3B-Instruct")
    wda_url = args.wda_url or os.getenv("PHONECLI_WDA_URL", "http://localhost:8100")

    # Select tasks
    try:
        task_ids = [int(x.strip()) for x in args.tasks.split(",")]
    except ValueError as e:
        print(f"Error: invalid task ID in '--tasks {args.tasks}': {e}")
        sys.exit(1)
    selected = [t for t in TASKS if t["id"] in task_ids]
    if not selected:
        print("Error: no matching tasks found")
        sys.exit(1)

    app_map = args.app_map if not args.no_macro else None

    # Verify WDA
    from phonecli.device import is_wda_ready
    if not is_wda_ready(wda_url):
        print(f"Error: WDA not ready at {wda_url}")
        sys.exit(1)

    print(f"Model: {model}")
    print(f"Tasks: {[t['id'] for t in selected]}")
    print(f"App map: {app_map or 'N/A (pure VLM)'}")
    print(f"Max rounds: {args.max_rounds}")

    results = run_eval(
        selected, app_map,
        max_rounds=args.max_rounds,
        request_interval=args.request_interval,
        wda_url=wda_url,
        task_dir=args.task_dir,
        api_key=api_key, api_base=api_base, model=model,
    )

    print_report(results)

    if args.output:
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\nResults saved to {args.output}")


if __name__ == "__main__":
    main()
