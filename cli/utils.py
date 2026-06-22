"""Shared utilities for the OpenPhone CLI."""

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

VERSION = "0.2.0"

# Cache for directly-loaded modules (avoids package __init__.py)
_module_cache: dict[str, Any] = {}


def _load_module_direct(name: str, filepath: str) -> Any:
    """Load a Python module from a file path without executing its package __init__.py."""
    if name in _module_cache:
        return _module_cache[name]
    spec = importlib.util.spec_from_file_location(name, filepath)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module {name} from {filepath}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod  # register so sub-imports within the module resolve
    spec.loader.exec_module(mod)
    _module_cache[name] = mod
    return mod


def _get_ios_agent_module(module_name: str) -> Any:
    """Load an ios_agent submodule without triggering ios_agent/__init__.py."""
    ios_dir = Path(__file__).parent.parent / "ios_agent"
    filepath = ios_dir / f"{module_name}.py"
    if not filepath.exists():
        raise ImportError(f"ios_agent.{module_name} not found at {filepath}")
    return _load_module_direct(f"ios_agent.{module_name}", str(filepath))


def import_ios_connection():
    """Import IOSConnection from ios_agent.connection (bypasses package init)."""
    return _get_ios_agent_module("connection").IOSConnection


def import_ios_screenshot():
    """Import screenshot functions from ios_agent.screenshot."""
    return _get_ios_agent_module("screenshot")


def import_ios_hierarchy():
    """Import hierarchy functions from ios_agent.hierarchy."""
    return _get_ios_agent_module("hierarchy")


def import_ios_actions():
    """Import IOSActionHandler from ios_agent.actions."""
    return _get_ios_agent_module("actions").IOSActionHandler


def print_json(data: dict) -> None:
    """Print data as JSON to stdout."""
    json.dump(data, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    sys.stdout.flush()


def success(data: dict | None = None) -> dict:
    """Build a success response envelope."""
    result = {"success": True}
    if data:
        result.update(data)
    return result


def error(message: str, code: str = "ERROR") -> dict:
    """Build an error response envelope."""
    return {"success": False, "error": {"code": code, "message": message}}


def print_result(data: dict, use_json: bool) -> None:
    """Print result in either JSON or human-readable format."""
    if use_json:
        print_json(data)
    else:
        if data.get("success") is False:
            err = data.get("error", {})
            print(f"Error [{err.get('code', 'UNKNOWN')}]: {err.get('message', 'Unknown error')}")
        else:
            print_human(data)


def print_human(data: dict) -> None:
    """Print result in human-readable format."""
    display = {k: v for k, v in data.items() if k != "success"}
    if not display:
        print("OK")
        return
    for key, value in display.items():
        if isinstance(value, (list, dict)):
            print(f"{key}: {json.dumps(value, ensure_ascii=False, indent=2)}")
        else:
            print(f"{key}: {value}")
