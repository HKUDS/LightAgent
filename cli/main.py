#!/usr/bin/env python3
"""
OpenPhone CLI — Unified command-line interface for AI phone automation.

    openphone run <task>       Autonomous task execution (Ralph Loop + VLM)
    openphone daemon            Interactive daemon mode
    openphone learn [app]       Record demo and extract navigation lessons
    openphone memory show|list|query   Manage user memory and experience log
    openphone snapshot           Capture screenshot + UI hierarchy
    openphone tap <ref>          Tap at coordinates, element, or fraction
    openphone type <text>        Type text into focused input
    openphone swipe <direction>  Swipe in a direction
    openphone press <key>        Press a system key (home, back)
    openphone open <app>         Launch an app
    openphone wait <seconds>     Wait for a duration
    openphone keyboard           Dismiss the on-screen keyboard

Usage:
    openphone --version
    openphone --help
    openphone <command> --help
"""

import argparse
import os
import sys
from pathlib import Path

# Ensure project root is on sys.path
_project_root = Path(__file__).parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from cli.utils import VERSION, print_result, success, error


def _register_all_parsers(subparsers):
    """Register all command subparsers (lazy import to avoid heavy deps on --version/--help)."""
    from cli.commands.device import register_parser as register_device
    from cli.commands.run import register_parser as register_run
    from cli.commands.memory import register_parser as register_memory

    register_device(subparsers)
    register_run(subparsers)
    register_memory(subparsers)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="openphone",
        description="OpenPhone CLI — AI phone automation for iOS devices.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Run 'openphone <command> --help' for detailed command usage.",
    )

    parser.add_argument(
        "--version", "-V", action="store_true",
        help="Show version and exit",
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output structured JSON (for AI agent consumption)",
    )
    parser.add_argument(
        "--wda-url",
        type=str,
        default=os.getenv("WDA_URL", "http://localhost:8100"),
        help="WebDriverAgent URL (default: http://localhost:8100)",
    )
    parser.add_argument(
        "--session-id",
        type=str,
        default=None,
        help="WDA session ID (auto-created if omitted)",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        title="commands",
        metavar="<command>",
    )

    # Fast path: handle --version and --help without importing command modules
    if argv is None:
        argv = sys.argv[1:]

    # Check for fast-path flags before importing heavy dependencies
    if "--version" in argv or "-V" in argv:
        print(f"openphone {VERSION}")
        return

    if "--help" in argv or "-h" in argv or not argv:
        # Register commands so help text is complete
        _register_all_parsers(subparsers)
        args = parser.parse_args(argv)
        if not args.command:
            parser.print_help()
        else:
            # --help for a specific command is handled by argparse automatically
            pass
        return

    # Normal path: register commands and parse
    _register_all_parsers(subparsers)
    args = parser.parse_args(argv)

    # No command given
    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Dispatch to command handler
    use_json = getattr(args, "json", False)

    try:
        result = args.func(args)
        print_result(result, use_json)
        if not result.get("success"):
            sys.exit(1)
    except ConnectionError as e:
        print_result(error(str(e), "CONNECTION_ERROR"), use_json)
        sys.exit(1)
    except KeyboardInterrupt:
        print_result(error("Interrupted by user", "INTERRUPTED"), use_json)
        sys.exit(130)
    except Exception as e:
        print_result(error(str(e), "UNEXPECTED_ERROR"), use_json)
        sys.exit(1)


if __name__ == "__main__":
    main()
