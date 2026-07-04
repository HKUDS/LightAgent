"""iOS device operations via WebDriverAgent (WDA) HTTP API.

All coordinates are in WDA logical points (not physical pixels).
WDA logical points are what you get from window/size (e.g. 390x844 for iPhone 14 Pro).
Screenshots are physical pixels (e.g. 1170x2532) but that's handled transparently.
"""

import base64
import os
import sys
import time
from typing import Optional, Tuple

import requests


def _wda_url_base(wda_url: str = None) -> str:
    return (wda_url or os.getenv("PHONECLI_WDA_URL", "http://localhost:8100")).rstrip("/")


def _wda_session_url(wda_url: str, session_id: str, endpoint: str) -> str:
    base = _wda_url_base(wda_url)
    return f"{base}/session/{session_id}/{endpoint}"


# ---------------------------------------------------------------------------
# Connection
# ---------------------------------------------------------------------------

def is_wda_ready(wda_url: str = None) -> bool:
    try:
        r = requests.get(f"{_wda_url_base(wda_url)}/status", timeout=5)
        return r.status_code == 200
    except Exception:
        return False


def create_session(wda_url: str = None) -> Tuple[bool, str]:
    """Create a WDA session. Returns (ok, session_id)."""
    try:
        r = requests.post(
            f"{_wda_url_base(wda_url)}/session",
            json={"capabilities": {}},
            timeout=30,
        )
        if r.status_code in (200, 201):
            data = r.json()
            sid = data.get("sessionId") or (data.get("value", {}) if isinstance(data.get("value"), dict) else {}).get("sessionId", "")
            if not sid and isinstance(data.get("value"), str):
                sid = data["value"]
            if not sid:
                return False, f"Could not extract session ID from response: {str(data)[:200]}"
            return True, sid
        return False, f"HTTP {r.status_code}: {r.text[:200]}"
    except Exception as e:
        return False, str(e)


# ---------------------------------------------------------------------------
# Screen info
# ---------------------------------------------------------------------------

def get_screen_size(wda_url: str = None, session_id: str = None) -> Tuple[int, int]:
    """Return WDA logical screen size (points)."""
    try:
        if session_id:
            url = _wda_session_url(wda_url, session_id, "window/size")
        else:
            url = f"{_wda_url_base(wda_url)}/window/size"
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            data = r.json()
            v = data.get("value", {})
            return v.get("width", 390), v.get("height", 844)
    except Exception:
        pass
    return 390, 844


# ---------------------------------------------------------------------------
# Screenshot
# ---------------------------------------------------------------------------

def take_screenshot(output_path: str, wda_url: str = None, session_id: str = None) -> bool:
    """Take a screenshot via WDA and save as PNG to output_path."""
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    try:
        if session_id:
            url = _wda_session_url(wda_url, session_id, "screenshot")
        else:
            url = f"{_wda_url_base(wda_url)}/screenshot"
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            return False
        data = r.json()
        b64 = data.get("value", "")
        if not b64:
            return False
        img_data = base64.b64decode(b64)
        with open(output_path, "wb") as f:
            f.write(img_data)
        return True
    except Exception as e:
        print(f"Screenshot error: {e}", file=sys.stderr)
        return False


# ---------------------------------------------------------------------------
# Accessibility tree (page source)
# ---------------------------------------------------------------------------

def dump_xml(output_path: str, wda_url: str = None, session_id: str = None) -> bool:
    """Dump iOS page source (XCUITest XML hierarchy) to output_path."""
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    try:
        if session_id:
            url = _wda_session_url(wda_url, session_id, "source")
        else:
            url = f"{_wda_url_base(wda_url)}/source"
        r = requests.get(url, timeout=15)
        if r.status_code != 200:
            return False
        data = r.json()
        source = data.get("value", "")
        # source may be a nested dict or directly a string
        if isinstance(source, dict):
            source = source.get("source") or source.get("value") or ""
        if not isinstance(source, str) or not source.strip():
            return False
        # Unescape
        source = source.strip().replace("\\n", "\n").replace("\\t", "\t").replace('\\"', '"')
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(source)
        return True
    except Exception as e:
        print(f"XML dump error: {e}", file=sys.stderr)
        return False


# ---------------------------------------------------------------------------
# Touch actions (WDA logical coordinates)
# ---------------------------------------------------------------------------

def tap(x: int, y: int, wda_url: str = None, session_id: str = None) -> bool:
    """Tap at logical coordinates (x, y)."""
    try:
        url = _wda_session_url(wda_url, session_id, "actions")
        payload = {
            "actions": [{
                "type": "pointer",
                "id": "finger1",
                "parameters": {"pointerType": "touch"},
                "actions": [
                    {"type": "pointerMove", "duration": 0, "x": x, "y": y},
                    {"type": "pointerDown", "button": 0},
                    {"type": "pause", "duration": 100},
                    {"type": "pointerUp", "button": 0},
                ],
            }]
        }
        r = requests.post(url, json=payload, timeout=10)
        time.sleep(0.5)
        return r.status_code in (200, 201)
    except Exception as e:
        print(f"Tap error: {e}", file=sys.stderr)
        return False


def long_press(x: int, y: int, duration_ms: int = 3000,
               wda_url: str = None, session_id: str = None) -> bool:
    """Long press at logical coordinates."""
    try:
        url = _wda_session_url(wda_url, session_id, "actions")
        payload = {
            "actions": [{
                "type": "pointer",
                "id": "finger1",
                "parameters": {"pointerType": "touch"},
                "actions": [
                    {"type": "pointerMove", "duration": 0, "x": x, "y": y},
                    {"type": "pointerDown", "button": 0},
                    {"type": "pause", "duration": duration_ms},
                    {"type": "pointerUp", "button": 0},
                ],
            }]
        }
        r = requests.post(url, json=payload, timeout=int(duration_ms / 1000) + 10)
        time.sleep(0.5)
        return r.status_code in (200, 201)
    except Exception as e:
        print(f"Long press error: {e}", file=sys.stderr)
        return False


def swipe(x1: int, y1: int, x2: int, y2: int,
          duration_ms: int = 400, wda_url: str = None, session_id: str = None) -> bool:
    """Swipe from (x1,y1) to (x2,y2) in logical coordinates."""
    try:
        url = _wda_session_url(wda_url, session_id, "wda/dragfromtoforduration")
        duration_s = max(duration_ms / 1000.0, 0.1)
        payload = {
            "fromX": x1, "fromY": y1,
            "toX": x2, "toY": y2,
            "duration": duration_s,
        }
        r = requests.post(url, json=payload, timeout=int(duration_s) + 10)
        time.sleep(0.5)
        return r.status_code in (200, 201)
    except Exception as e:
        print(f"Swipe error: {e}", file=sys.stderr)
        return False


# ---------------------------------------------------------------------------
# Text input
# ---------------------------------------------------------------------------

def input_text(text: str, wda_url: str = None, session_id: str = None) -> bool:
    """Type text via WDA keyboard API."""
    try:
        url = _wda_session_url(wda_url, session_id, "wda/keys")
        r = requests.post(url, json={"value": list(text)}, timeout=30)
        return r.status_code in (200, 201)
    except Exception as e:
        print(f"Text input error: {e}", file=sys.stderr)
        return False


# ---------------------------------------------------------------------------
# Navigation
# ---------------------------------------------------------------------------

def back(wda_url: str = None, session_id: str = None) -> bool:
    """iOS back gesture: swipe from left edge to center-right."""
    w, h = get_screen_size(wda_url, session_id)
    return swipe(0, h // 2, w // 3, h // 2, duration_ms=300,
                 wda_url=wda_url, session_id=session_id)


def home(wda_url: str = None, session_id: str = None) -> bool:
    """Go to home screen via WDA."""
    try:
        r = requests.post(f"{_wda_url_base(wda_url)}/wda/homescreen", timeout=10)
        time.sleep(1)
        return r.status_code in (200, 201)
    except Exception as e:
        print(f"Home error: {e}", file=sys.stderr)
        return False


def launch_app(bundle_id: str, wda_url: str = None, session_id: str = None) -> bool:
    """Launch an iOS app by bundle ID (e.g. com.apple.Preferences)."""
    try:
        url = _wda_session_url(wda_url, session_id, "wda/apps/launch")
        r = requests.post(url, json={"bundleId": bundle_id}, timeout=10)
        time.sleep(3)
        return r.status_code in (200, 201)
    except Exception as e:
        print(f"Launch error: {e}", file=sys.stderr)
        return False


def get_current_app(wda_url: str = None, session_id: str = None) -> str:
    """Get the current foreground app bundle ID."""
    try:
        if session_id:
            url = _wda_session_url(wda_url, session_id, "wda/activeAppInfo")
        else:
            url = f"{_wda_url_base(wda_url)}/wda/activeAppInfo"
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            data = r.json()
            value = data.get("value", {})
            bundle_id = value.get("bundleId", "")
            if bundle_id:
                return bundle_id
    except Exception:
        pass
    return "unknown"


def force_stop(bundle_id: str, wda_url: str = None, session_id: str = None) -> bool:
    """Terminate an iOS app via WDA."""
    try:
        url = _wda_session_url(wda_url, session_id, "wda/apps/terminate")
        r = requests.post(url, json={"bundleId": bundle_id}, timeout=10)
        time.sleep(1)
        return r.status_code in (200, 201)
    except Exception as e:
        print(f"Force stop error: {e}", file=sys.stderr)
        return False


# ---------------------------------------------------------------------------
# Known iOS bundle IDs
# ---------------------------------------------------------------------------

KNOWN_BUNDLE_IDS = {
    "Safari": "com.apple.mobilesafari",
    "备忘录": "com.apple.mobilenotes",
    "Notes": "com.apple.mobilenotes",
    "Settings": "com.apple.Preferences",
    "Messages": "com.apple.MobileSMS",
    "Mail": "com.apple.mobilemail",
    "Photos": "com.apple.mobileslideshow",
    "Camera": "com.apple.camera",
    "Clock": "com.apple.mobiletimer",
    "Calendar": "com.apple.mobilecal",
    "Maps": "com.apple.Maps",
    "Music": "com.apple.Music",
    "App Store": "com.apple.AppStore",
    "Reminders": "com.apple.reminders",
    "Weather": "com.apple.weather",
    "Contacts": "com.apple.MobileAddressBook",
    "FaceTime": "com.apple.facetime",
    "Phone": "com.apple.mobilephone",
    "Health": "com.apple.Health",
    "Wallet": "com.apple.Passbook",
    "Files": "com.apple.DocumentsApp",
    "TV": "com.apple.tv",
    "Podcasts": "com.apple.podcasts",
    "News": "com.apple.news",
    "Shortcuts": "com.apple.shortcuts",
    "Watch": "com.apple.Bridge",
    "Tips": "com.apple.tips",
    "Translate": "com.apple.Translate",
}


def resolve_bundle_id(name: str) -> Optional[str]:
    """Resolve an app name to bundle ID. Returns None if not found."""
    if "." in name and name.count(".") >= 2:
        return name  # already a bundle ID
    return KNOWN_BUNDLE_IDS.get(name) or KNOWN_BUNDLE_IDS.get(name.capitalize())
