#!/usr/bin/env python3
"""Entry point for running a phone agent task on iOS via WebDriverAgent.

Usage:
    python run.py --task "Turn on wifi" --app-map settings_map.yaml
    python run.py --task "Open Safari and search for weather" --max-rounds 30
    python run.py --task "Check battery level" --app-map settings_map.yaml --list-ops

Environment variables:
    PHONECLI_LLM_API_KEY / API_KEY       — LLM API key
    PHONECLI_LLM_API_BASE / API_BASE     — LLM API base URL
    PHONECLI_LLM_MODEL / MODEL_NAME      — LLM model name
    PHONECLI_VLM_API_KEY                 — VLM API key (falls back to LLM key)
    PHONECLI_VLM_API_BASE                — VLM API base URL
    PHONECLI_VLM_MODEL                   — VLM model name
    PHONECLI_WDA_URL                     — WebDriverAgent URL (default: http://localhost:8100)
    PHONECLI_TASK_DIR                    — Log directory (default: ./phonecli_logs)
"""

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from phonecli.agent import PhoneAgent, AgentConfig


def _discover_app_maps() -> list[str]:
    """Auto-discover all *.yaml app maps in the package's app_maps directory.

    Returns sorted absolute paths. Returns empty list if the directory
    does not exist or contains no YAML files.
    """
    maps_dir = Path(__file__).parent / "app_maps"
    if not maps_dir.is_dir():
        return []
    return sorted(str(p) for p in maps_dir.glob("*.yaml"))


def main():
    parser = argparse.ArgumentParser(
        description="Phone Agent — coordinate-based iOS phone automation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--task", "-t", required=False, help="Task description")
    parser.add_argument("--app-map", "-m", default=None, action="append",
                        help="Path to app map YAML (repeatable for multi-app tasks)")
    parser.add_argument("--interactive", "-i", action="store_true", default=False,
                        help="Run in interactive daemon mode: connect once, accept multiple tasks")
    parser.add_argument("--max-rounds", type=int, default=25,
                        help="Maximum interaction rounds")
    parser.add_argument("--request-interval", type=float, default=3.0,
                        help="Interval between requests in seconds")
    parser.add_argument("--wda-url", default=None,
                        help="WebDriverAgent URL (default: http://localhost:8100)")
    parser.add_argument("--task-dir", default=None,
                        help="Directory for logs and screenshots")
    parser.add_argument("--list-ops", action="store_true",
                        help="List available operations in the app map and exit")
    parser.add_argument("--no-macro", action="store_true",
                        help="Skip macro routing, go directly to VLM")

    # LLM config
    parser.add_argument("--llm-api-key", default=None)
    parser.add_argument("--llm-api-base", default=None)
    parser.add_argument("--llm-model", default=None)
    parser.add_argument("--vlm-api-key", default=None)
    parser.add_argument("--vlm-api-base", default=None)
    parser.add_argument("--vlm-model", default=None)

    args = parser.parse_args()

    if args.list_ops:
        maps = args.app_map or _discover_app_maps()
        if not maps:
            print("Error: --app-map or phonecli/app_maps/*.yaml required with --list-ops")
            sys.exit(1)
        _list_operations(maps[0])
        return

    # Validate: need either --task or --interactive
    if not args.interactive and not args.task:
        print("Error: Provide --task <description> or --interactive for daemon mode.")
        sys.exit(1)

    if args.interactive and args.task:
        print("[Run] Warning: --task is ignored in --interactive mode.")

    # Build config
    config = AgentConfig.from_env()
    config.max_rounds = args.max_rounds
    config.request_interval = args.request_interval

    if args.wda_url:
        config.wda_url = args.wda_url
    if args.task_dir:
        config.task_dir = args.task_dir
    if args.llm_api_key:
        config.llm_api_key = args.llm_api_key
    if args.llm_api_base:
        config.llm_api_base = args.llm_api_base
    if args.llm_model:
        config.llm_model = args.llm_model
    if args.vlm_api_key:
        config.vlm_api_key = args.vlm_api_key
    if args.vlm_api_base:
        config.vlm_api_base = args.vlm_api_base
    if args.vlm_model:
        config.vlm_model = args.vlm_model

    # Wire up app maps (None or list[str])
    if args.no_macro:
        app_maps = None
    elif args.app_map:
        app_maps = args.app_map
    else:
        app_maps = _discover_app_maps() or None

    # Route to interactive daemon or single-task mode
    if args.interactive:
        from phonecli.daemon import run_daemon
        run_daemon(config, app_maps)
        return

    # --- Single-task mode ---
    # Verify WDA is ready
    from phonecli.device import is_wda_ready
    if not is_wda_ready(config.wda_url):
        print(f"Error: WebDriverAgent is not ready at {config.wda_url}")
        print("Ensure WDA is running on your iOS device and the URL is correct.")
        sys.exit(1)

    if app_maps:
        print(f"[Run] App maps: {', '.join(app_maps)}")
    print(f"[Run] Config: llm={config.llm_model} @ {config.llm_api_base}")
    print(f"[Run] Config: vlm={config.vlm_model} @ {config.vlm_api_base}")
    print(f"[Run] WDA: {config.wda_url}")
    print(f"[Run] Task dir: {config.task_dir}")
    print()

    agent = PhoneAgent(config)
    result = agent.run(args.task, app_maps)

    print()
    print("=" * 50)
    print(f"Status:   {result['status']}")
    print(f"Rounds:   {result['rounds']}")
    print(f"VLM steps:{result['vlm_steps']}")
    print("=" * 50)


def _list_operations(app_map_path: str):
    from phonecli.app_map import AppMap
    if not os.path.exists(app_map_path):
        print(f"Error: file not found: {app_map_path}")
        sys.exit(1)
    am = AppMap(app_map_path)
    ops = am.build_operations()
    print(f"App: {am.app_name} ({am.package})")
    print(f"Screens: {len(am.screens)}")
    print(f"Operations: {len(ops)}")
    print()
    print(am.format_ops_catalog(ops))


if __name__ == "__main__":
    main()
