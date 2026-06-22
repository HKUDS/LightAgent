"""Agent-driven device commands for the OpenPhone CLI.

These commands are designed for external AI agents (Claude Code, Codex, etc.)
to control an iOS device through the CLI. Each command does one atomic operation.

Usage:
    openphone snapshot [--json]
    openphone tap <ref> [--json]
    openphone type <text> [--json]
    openphone swipe <direction> [--json]
    openphone press <key> [--json]
    openphone open <app> [--json]
"""

import argparse
import os

from cli.utils import (
    import_ios_connection,
    import_ios_screenshot,
    import_ios_hierarchy,
    import_ios_actions,
)

# Lazily resolved on first use
_ios_connection = None
_ios_screenshot = None
_ios_hierarchy = None
_ios_actions = None


def _get_connection():
    global _ios_connection
    if _ios_connection is None:
        _ios_connection = import_ios_connection()
    return _ios_connection


def _get_screenshot():
    global _ios_screenshot
    if _ios_screenshot is None:
        _ios_screenshot = import_ios_screenshot()
    return _ios_screenshot


def _get_hierarchy():
    global _ios_hierarchy
    if _ios_hierarchy is None:
        _ios_hierarchy = import_ios_hierarchy()
    return _ios_hierarchy


def _get_actions():
    global _ios_actions
    if _ios_actions is None:
        _ios_actions = import_ios_actions()
    return _ios_actions


def _get_wda_url(args: argparse.Namespace) -> str:
    return args.wda_url or os.getenv("WDA_URL", "http://localhost:8100")


def _connect(wda_url: str):
    """Connect to WDA and return (connection, handler, session_id)."""
    IOSConnection = _get_connection()
    IOSActionHandler = _get_actions()
    conn = IOSConnection(wda_url)
    if not conn.is_wda_ready():
        raise ConnectionError(f"WebDriverAgent not ready at {wda_url}")
    ok, result = conn.start_wda_session()
    session_id = result if ok and result and result != "session_started" else None
    handler = IOSActionHandler(wda_url=wda_url, session_id=session_id)
    return conn, handler, session_id


# ---------------------------------------------------------------------------
# snapshot
# ---------------------------------------------------------------------------

def cmd_snapshot(args: argparse.Namespace) -> dict:
    """Capture screenshot + UI hierarchy + interactive element list."""
    wda_url = _get_wda_url(args)
    conn, handler, session_id = _connect(wda_url)

    screenshot_mod = _get_screenshot()
    hierarchy_mod = _get_hierarchy()

    screenshot = screenshot_mod.get_screenshot(wda_url, session_id)
    xml_source = hierarchy_mod.get_page_source(wda_url, session_id)
    elements = hierarchy_mod.get_ios_elements(xml_source) if xml_source else []

    current_app: str = ""
    try:
        current_app = handler.get_current_app()
    except Exception:
        pass

    elem_list = []
    for i, elem in enumerate(elements):
        (x1, y1), (x2, y2) = elem.bbox
        w = x2 - x1
        h = y2 - y1
        elem_list.append({
            "ref": f"@e{i + 1}",
            "type": elem.element_type,
            "name": elem.name,
            "label": elem.label,
            "identifier": elem.identifier,
            "bounds": {"x": x1, "y": y1, "width": w, "height": h},
            "center": {"x": (x1 + x2) // 2, "y": (y1 + y2) // 2},
            "enabled": True,
        })

    return {
        "success": True,
        "screenshot": screenshot.base64_data,
        "width": screenshot.width,
        "height": screenshot.height,
        "app": current_app,
        "elements": elem_list,
        "element_count": len(elem_list),
    }


# ---------------------------------------------------------------------------
# tap
# ---------------------------------------------------------------------------

def cmd_tap(args: argparse.Namespace) -> dict:
    """Tap at a position, element ref, or screen fraction.

    Supported ref formats:
        "@e3"       - element reference from snapshot
        "200,300"   - pixel coordinates
        "0.5,0.5"   - fractional (normalized) coordinates
    """
    wda_url = _get_wda_url(args)
    _, handler, _ = _connect(wda_url)

    ref: str = args.ref

    if ref.startswith("@"):
        # Element reference: re-snapshot to resolve
        hierarchy_mod = _get_hierarchy()
        xml_source = hierarchy_mod.get_page_source(wda_url)
        if not xml_source:
            return {"success": False, "error": {"code": "NO_XML", "message": "Failed to get page source"}}
        elements = hierarchy_mod.get_ios_elements(xml_source)
        try:
            idx = int(ref[2:]) - 1 if ref.startswith("@e") else int(ref[1:]) - 1
        except ValueError:
            return {"success": False, "error": {"code": "INVALID_REF", "message": f"Invalid element ref: {ref}"}}
        if idx < 0 or idx >= len(elements):
            return {"success": False, "error": {"code": "INVALID_REF", "message": f"Element not found: {ref}"}}
        elem = elements[idx]
        (x1, y1), (x2, y2) = elem.bbox
        x, y = (x1 + x2) // 2, (y1 + y2) // 2
    elif "," in ref:
        parts = ref.split(",")
        if len(parts) != 2:
            return {"success": False, "error": {"code": "INVALID_REF", "message": f"Expected format: x,y or @eN. Got: {ref}"}}
        try:
            a, b = float(parts[0].strip()), float(parts[1].strip())
        except ValueError:
            return {"success": False, "error": {"code": "INVALID_REF", "message": f"Invalid coordinates: {ref}"}}
        if 0 < a <= 1 and 0 < b <= 1:
            # Fractional coordinates
            actions_mod = _get_actions()
            screen_w, screen_h = handler.get_screen_size()
            x, y = int(a * screen_w * actions_mod.SCALE_FACTOR), int(b * screen_h * actions_mod.SCALE_FACTOR)
        else:
            x, y = int(a), int(b)
    else:
        return {"success": False, "error": {"code": "INVALID_REF", "message": f"Unsupported ref format: {ref}. Use @eN, x,y, or 0.x,0.y"}}

    ok = handler.tap(x, y)
    return {"success": ok, "x": x, "y": y}


# ---------------------------------------------------------------------------
# type
# ---------------------------------------------------------------------------

def cmd_type(args: argparse.Namespace) -> dict:
    """Type text into the focused input field."""
    wda_url = _get_wda_url(args)
    _, handler, _ = _connect(wda_url)

    ok = handler.type_text(args.text)
    return {"success": ok, "text": args.text}


# ---------------------------------------------------------------------------
# swipe
# ---------------------------------------------------------------------------

SWIPE_DIRECTIONS = {
    "up": (0.5, 0.8, 0.5, 0.2),
    "down": (0.5, 0.2, 0.5, 0.8),
    "left": (0.8, 0.5, 0.2, 0.5),
    "right": (0.2, 0.5, 0.8, 0.5),
}


def cmd_swipe(args: argparse.Namespace) -> dict:
    """Swipe in a direction."""
    wda_url = _get_wda_url(args)
    _, handler, _ = _connect(wda_url)

    direction = args.direction.lower()
    if direction not in SWIPE_DIRECTIONS:
        return {"success": False, "error": {"code": "INVALID_DIRECTION",
                "message": f"Unknown direction: {direction}. Use: {', '.join(SWIPE_DIRECTIONS)}"}}

    actions_mod = _get_actions()
    screen_w, screen_h = handler.get_screen_size()
    fx1, fy1, fx2, fy2 = SWIPE_DIRECTIONS[direction]
    start_x = int(fx1 * screen_w * actions_mod.SCALE_FACTOR)
    start_y = int(fy1 * screen_h * actions_mod.SCALE_FACTOR)
    end_x = int(fx2 * screen_w * actions_mod.SCALE_FACTOR)
    end_y = int(fy2 * screen_h * actions_mod.SCALE_FACTOR)

    ok = handler.swipe(start_x, start_y, end_x, end_y)
    return {"success": ok, "direction": direction}


# ---------------------------------------------------------------------------
# press
# ---------------------------------------------------------------------------

PRESS_KEYS = {"home", "back"}


def cmd_press(args: argparse.Namespace) -> dict:
    """Press a system key (home, back)."""
    wda_url = _get_wda_url(args)
    _, handler, _ = _connect(wda_url)

    key = args.key.lower()
    if key not in PRESS_KEYS:
        return {"success": False, "error": {"code": "INVALID_KEY",
                "message": f"Unknown key: {key}. Use: {', '.join(sorted(PRESS_KEYS))}"}}

    if key == "home":
        ok = handler.home()
    elif key == "back":
        ok = handler.back()
    else:
        ok = False

    return {"success": ok, "key": key}


# ---------------------------------------------------------------------------
# open
# ---------------------------------------------------------------------------

def cmd_open(args: argparse.Namespace) -> dict:
    """Launch an app by name."""
    wda_url = _get_wda_url(args)
    _, handler, _ = _connect(wda_url)

    ok = handler.launch_app(args.app)
    return {"success": ok, "app": args.app}


# ---------------------------------------------------------------------------
# wait
# ---------------------------------------------------------------------------

def cmd_wait(args: argparse.Namespace) -> dict:
    """Wait for a specified duration (seconds)."""
    import time
    duration: float = args.seconds
    time.sleep(duration)
    return {"success": True, "waited": duration}


# ---------------------------------------------------------------------------
# keyboard
# ---------------------------------------------------------------------------

def cmd_keyboard(args: argparse.Namespace) -> dict:
    """Dismiss the on-screen keyboard."""
    wda_url = _get_wda_url(args)
    _, handler, _ = _connect(wda_url)

    ok = handler.hide_keyboard()
    return {"success": ok}


# ---------------------------------------------------------------------------
# Subcommand registration
# ---------------------------------------------------------------------------

def register_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register device subcommands on the given subparsers."""

    # ---- snapshot ----
    p_snapshot = subparsers.add_parser("snapshot", help="Capture screenshot and UI hierarchy")
    p_snapshot.set_defaults(func=cmd_snapshot)

    # ---- tap ----
    p_tap = subparsers.add_parser("tap", help="Tap at coordinates, element ref, or fraction")
    p_tap.add_argument("ref", help="Tap target: @eN (element), x,y (pixels), or 0.x,0.y (fraction)")
    p_tap.set_defaults(func=cmd_tap)

    # ---- type ----
    p_type = subparsers.add_parser("type", help="Type text into the focused input field")
    p_type.add_argument("text", help="Text to type")
    p_type.set_defaults(func=cmd_type)

    # ---- swipe ----
    p_swipe = subparsers.add_parser("swipe", help="Swipe in a direction")
    p_swipe.add_argument("direction", help=f"Swipe direction: {', '.join(SWIPE_DIRECTIONS)}")
    p_swipe.set_defaults(func=cmd_swipe)

    # ---- press ----
    p_press = subparsers.add_parser("press", help="Press a system key")
    p_press.add_argument("key", help=f"Key to press: {', '.join(sorted(PRESS_KEYS))}")
    p_press.set_defaults(func=cmd_press)

    # ---- open ----
    p_open = subparsers.add_parser("open", help="Launch an app by name")
    p_open.add_argument("app", help="App name (e.g. Safari, Settings, WeChat)")
    p_open.set_defaults(func=cmd_open)

    # ---- wait ----
    p_wait = subparsers.add_parser("wait", help="Wait for a specified duration in seconds")
    p_wait.add_argument("seconds", type=float, help="Duration to wait (seconds, e.g. 1.5)")
    p_wait.set_defaults(func=cmd_wait)

    # ---- keyboard ----
    p_kb = subparsers.add_parser("keyboard", help="Dismiss the on-screen keyboard")
    p_kb.set_defaults(func=cmd_keyboard)
