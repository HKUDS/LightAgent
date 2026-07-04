"""App map builder — crawl an iOS app via WDA and generate a YAML app map.

Algorithm: BFS crawl from screen_0.
  1. Disable auto-lock, launch app, dump + scroll screen_0.
  2. BFS: for each element, navigate via FULL path replay, tap, dump new screen.
  3. Record edges (leads_to) and macros (full paths from screen_0).
  4. Background keepalive thread prevents screen sleep.
  5. Output compact YAML (platform-agnostic action format).
"""

import json
import os
import re
import sys
import threading
import time
from typing import Optional

import yaml


# ---------------------------------------------------------------------------
# WDA helpers
# ---------------------------------------------------------------------------

def _dump_xml_str(wda_url: str, session_id: str) -> Optional[str]:
    import requests
    try:
        url = f"{wda_url.rstrip('/')}/session/{session_id}/source"
        r = requests.get(url, timeout=15)
        if r.status_code != 200:
            return None
        data = r.json()
        source = data.get("value", "")
        if isinstance(source, dict):
            source = source.get("source") or source.get("value") or ""
        if not source or not isinstance(source, str):
            return None
        return source.strip().replace("\\n", "\n").replace("\\t", "\t").replace('\\"', '"')
    except Exception:
        return None


# WDA helpers optimized for build speed (no sleeps, explicit URL, no env fallback).
# device.py has the full-featured versions used by agent/CLI.
def _wda_tap(x: int, y: int, wda_url: str, session_id: str):
    import requests
    url = f"{wda_url.rstrip('/')}/session/{session_id}/actions"
    payload = {
        "actions": [{
            "type": "pointer", "id": "finger1",
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
    return r.status_code == 200


def _wda_swipe(x1: int, y1: int, x2: int, y2: int, wda_url: str, session_id: str):
    import requests
    url = f"{wda_url.rstrip('/')}/session/{session_id}/wda/dragfromtoforduration"
    payload = {"fromX": x1, "fromY": y1, "toX": x2, "toY": y2, "duration": 0.4}
    r = requests.post(url, json=payload, timeout=10)
    return r.status_code == 200


def _wda_launch(bundle_id: str, wda_url: str, session_id: str):
    import requests
    url = f"{wda_url.rstrip('/')}/session/{session_id}/wda/apps/launch"
    r = requests.post(url, json={"bundleId": bundle_id}, timeout=10)
    return r.status_code == 200


def _wda_terminate(bundle_id: str, wda_url: str, session_id: str):
    import requests
    url = f"{wda_url.rstrip('/')}/session/{session_id}/wda/apps/terminate"
    r = requests.post(url, json={"bundleId": bundle_id}, timeout=10)
    return r.status_code == 200


def _get_screen_size_wda(wda_url: str, session_id: str) -> tuple:
    import requests
    try:
        url = f"{wda_url.rstrip('/')}/session/{session_id}/window/size"
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            v = r.json().get("value", {})
            return v.get("width", 390), v.get("height", 844)
    except Exception:
        pass
    return 390, 844


# ---------------------------------------------------------------------------
# Keep-alive thread
# ---------------------------------------------------------------------------

def _start_keepalive(wda_url: str, session_id: str, interval: int = 30):
    """Background thread: periodically ping WDA to prevent auto-lock.

    Primary: idleTimerDisabled (called once before build).
    Fallback: periodic centre tap if idleTimerDisabled is unsupported.
    """
    stopped = threading.Event()

    def _loop():
        import requests
        base = wda_url.rstrip("/")
        # Try idleTimerDisabled first
        try:
            r = requests.post(f"{base}/wda/settings",
                              json={"settings": {"idleTimerDisabled": True}},
                              timeout=10)
            if r.status_code in (200, 201):
                print("[Keepalive] idleTimerDisabled: ON (no taps needed)")
                # Still ping status to keep WDA HTTP session alive
                while not stopped.wait(interval * 2):
                    try:
                        requests.get(f"{base}/status", timeout=5)
                    except Exception:
                        pass
                return
        except Exception:
            pass

        # Fallback: safe status-bar swipe (won't trigger UI elements)
        print(f"[Keepalive] Falling back to safe swipe (every {interval}s)")
        w, h = _get_screen_size_wda(wda_url, session_id)
        sy = h // 40  # ~22px, well within status bar
        while not stopped.wait(interval):
            try:
                _wda_swipe(5, sy, 15, sy, wda_url, session_id)
            except Exception:
                pass

    t = threading.Thread(target=_loop, daemon=True)
    t.start()
    return stopped


# ---------------------------------------------------------------------------
# Element parsing (iOS XCUITest XML)
# ---------------------------------------------------------------------------

def _parse_elements_ios(xml_str: str) -> list[dict]:
    interactive_types = [
        'XCUIElementTypeButton', 'XCUIElementTypeCell',
        'XCUIElementTypeTextField', 'XCUIElementTypeSecureTextField',
        'XCUIElementTypeSearchField', 'XCUIElementTypeSwitch',
        'XCUIElementTypeTab', 'XCUIElementTypeLink',
        'XCUIElementTypeStaticText', 'XCUIElementTypeImage',
        'XCUIElementTypeIcon',
    ]
    elems = []
    seen_keys = set()
    for itype in interactive_types:
        for tag_match in re.finditer(rf'<{itype}\b([^>]*?)/>', xml_str):
            attrs = tag_match.group(0)
            label_match = re.search(r'label="([^"]*)"', attrs)
            name_match = re.search(r'name="([^"]*)"', attrs)
            x_match = re.search(r'\bx="(\d+)"', attrs)
            y_match = re.search(r'\by="(\d+)"', attrs)
            w_match = re.search(r'width="(\d+)"', attrs)
            h_match = re.search(r'height="(\d+)"', attrs)
            if not (x_match and y_match and w_match and h_match):
                continue
            x = int(x_match.group(1))
            y = int(y_match.group(1))
            w = int(w_match.group(1))
            h = int(h_match.group(1))
            if w <= 0 or h <= 0:
                continue
            text = label_match.group(1) if label_match else ""
            if not text and name_match:
                text = name_match.group(1)
            no_text = ("chevron", "additional", "dictate")
            if text.lower().startswith(no_text):
                continue
            if not text:
                continue
            key = (x // 5, y // 5, text.lower())
            if key in seen_keys:
                continue
            seen_keys.add(key)
            elems.append({
                "text": text.strip(),
                "center": (x + w // 2, y + h // 2),
            })
    return elems


# ---------------------------------------------------------------------------
# Element filtering
# ---------------------------------------------------------------------------

_DYNAMIC_PATTERNS = [
    r'^\d{1,2}:\d{2}$', r'^\d{1,2}:\d{2}\s*[AP]M$',
    r'^\d+\s*min\b', r'^\d+\s*(hour|hr|day|week|month|year)s?\b',
    r'\b\d{1,2}/\d{1,2}/\d{2,4}\b', r'^\d{1,3}\s*%$', r'^\d+$',
    r'^\d+\s*(messages|notifications|items|results?|emails?)$',
    r'^just now$', r'^now$', r'^today$', r'^yesterday$',
    r'^\d+[\.\d]*\s*(GB|MB|KB|TB)$',
    r'^(on|off)$',  # toggle states — dynamic values, not stable UI
    # --- New patterns for social media content ---
    r'^[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}$',  # UUID
    r'^[\d,]+$',               # comma-separated counts: 1,159 / 5,408
    r'^\d+\s*/\s*\d+$',         # image carousel: 1/2, 3/4
    r'^\d+[\.\d]*\s*(km|m|mi|mile|公里|米)$',  # distance: 1.8km, 500m
    r'^\d+\s*(分钟|小时|天|周|月|年)前$',       # Chinese relative time
    r'^\d+\s*(赞|评论|收藏|转发|粉丝|看过|浏览)$',  # Chinese stat labels
]

SKIP_TEXTS = {
    "", "system", "button", "image", "icon", "chevron",
    "navigate up", "more options", "clear", "dismiss",
    "profile picture", "learn more", "back", "cancel",
    "search",  # "Search" field label — not a navigable item
}


def _is_dynamic(text: str) -> bool:
    for pat in _DYNAMIC_PATTERNS:
        if re.match(pat, text, re.IGNORECASE):
            return True
    return False


def _should_skip(text: str, profile_filter=None, preserve_set=None) -> bool:
    t = text.lower().strip()
    if t in SKIP_TEXTS:
        return True
    if len(t) <= 1:
        return True
    # Preserve navigation elements first (before generic dynamic patterns)
    if preserve_set and t in preserve_set:
        return False
    # App-specific profile patterns
    if profile_filter and profile_filter(text):
        return True
    # Generic dynamic patterns
    if _is_dynamic(text):
        return True
    return False


def _build_signature(elements: list[dict], max_items: int = 10,
                     profile_filter=None, preserve_set=None) -> str:
    stable = []
    for e in elements:
        text = e["text"].strip()
        if not _should_skip(text, profile_filter, preserve_set):
            stable.append(text.lower())
        if len(stable) >= max_items:
            break
    return "||".join(sorted(stable))


# ---------------------------------------------------------------------------
# PII redaction
# ---------------------------------------------------------------------------

# Patterns to detect personal screens
_EMAIL_RE = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
_PHONE_RE = re.compile(r'\+?\d[\d\s\xa0\-]{7,}')
_PAYMENT_KEYS = ('支付宝', 'alipay', 'paypal', '微信支付', 'apple pay', 'unionpay', '云闪付')
_DEVICE_RE = re.compile(r'.{1,5}的\s*(Apple\s*Watch|iPhone|iPad|Mac|AirPods|HomePod)')


def _detect_pii(screens: list[dict]) -> set:
    """Return the set of screen IDs that contain PII."""
    personal_screens = set()
    for screen in screens:
        texts = " ".join(e["text"] for e in screen["elements"])
        if _EMAIL_RE.search(texts):
            personal_screens.add(screen["id"])
        elif _PHONE_RE.search(texts):
            personal_screens.add(screen["id"])
        elif any(kw in texts.lower() for kw in _PAYMENT_KEYS):
            personal_screens.add(screen["id"])
        elif _DEVICE_RE.search(texts):
            personal_screens.add(screen["id"])
    return personal_screens


def _redact_screens(screens: list[dict]) -> list[dict]:
    """Replace PII texts with placeholders. Returns modified copy.

    Two-pass approach:
      1. Detect personal screens, collect the specific PII text values found.
      2. Replace those values globally across ALL screens.
    """
    personal = _detect_pii(screens)
    if not personal:
        return screens

    # Pass 1: collect PII text values from personal screens
    emails = set()
    phones = set()
    payments = set()
    devices = set()
    names = set()
    for screen in screens:
        if screen["id"] not in personal:
            continue
        for e in screen["elements"]:
            t = e["text"]
            if _EMAIL_RE.search(t):
                emails.add(t)
            elif _PHONE_RE.search(t):
                phones.add(t)
            elif any(kw in t.lower() for kw in _PAYMENT_KEYS):
                payments.add(t)
            elif _DEVICE_RE.search(t):
                devices.add(t)
            elif 2 <= len(t) <= 5 and '一' <= t[0] <= '鿿' and all('一' <= c <= '鿿' for c in t):
                # Chinese name candidate — collect for global replacement
                # Skip known system labels
                skip = ("设置", "显示", "通知", "通用", "邮件", "相机", "日历",
                        "照片", "时钟", "天气", "地图", "音乐", "钱包", "健康",
                        "文件", "备忘", "通讯", "信息", "电话", "隐私", "安全",
                        "密码", "蓝牙", "无线", "蜂窝", "隔空", "隔空投送",
                        "家人", "家人共享", "屏幕", "控制", "个人", "专注",
                        "声音", "触感", "亮度", "亮度与", "主屏幕",
                        "搜索", "待机", "墙纸", "面容", "面容ID", "紧急",
                        "软件", "关于", "键盘", "字体", "词典", "自动",
                        "日期", "时间", "语言", "地区", "还原", "传输",
                        "苹果", "苹果智能")
                if t not in skip:
                    names.add(t)

    # Pass 2: replace globally (also match names appearing with suffixes)
    def _is_name_match(text: str) -> bool:
        if text in names:
            return True
        # e.g. "蒋杨钦 (You)" matches base name "蒋杨钦"
        for name in names:
            if text.startswith(name):
                return True
        return False

    changed = 0
    for screen in screens:
        for e in screen["elements"]:
            t = e["text"]
            if t in emails:
                e["text"] = "[Email]"; changed += 1
            elif t in phones:
                e["text"] = "[Phone]"; changed += 1
            elif t in payments:
                e["text"] = "[Payment]"; changed += 1
            elif t in devices:
                e["text"] = "[Device]"; changed += 1
            elif _is_name_match(t):
                e["text"] = "[Account]"; changed += 1

    if changed:
        screen_ids = ", ".join(sorted(personal))
        print(f"[Build] Redacted {changed} PII fields on screens: {screen_ids}")
    return screens


# ---------------------------------------------------------------------------
# LLM element classification — distinguish fixed UI from dynamic content
# ---------------------------------------------------------------------------

def _classify_elements_with_llm(
    elements: list[dict],
    app_name: str,
    api_key: str = "EMPTY",
    api_base: str = "http://localhost:8002/v1",
    model: str = "Qwen/Qwen2.5-3B-Instruct",
) -> tuple:
    """Use LLM to classify elements as STABLE (fixed UI) vs DYNAMIC (content).

    Returns (stable_elements, dynamic_elements) — both lists of dicts.
    Falls back to all-stable on LLM error.
    """
    if not elements:
        return elements, []

    from phonecli.llm_client import text_completion
    from phonecli.prompts import ELEMENT_CLASSIFY_PROMPT

    text_list = "\n".join(e["text"] for e in elements)
    system_prompt = ELEMENT_CLASSIFY_PROMPT.format(app_name=app_name)
    user_prompt = f"Elements:\n{text_list}"

    try:
        time.sleep(0.3)  # throttle to avoid rate limiting
        rsp = text_completion(system_prompt, user_prompt,
                              api_key=api_key, api_base=api_base, model=model,
                              max_tokens=2048, temperature=0.0)
        stable_set = set()
        for line in rsp.strip().splitlines():
            line = line.strip()
            if line.upper().startswith("STABLE|"):
                stable_set.add(line.split("|", 1)[1].strip())
    except Exception as e:
        print(f"[Build] LLM classification failed: {e}")
        return elements, []

    stable, dynamic = [], []
    for e in elements:
        if e["text"] in stable_set:
            stable.append(e)
        else:
            dynamic.append(e)

    print(f"[Build]   classified: {len(stable)} stable, {len(dynamic)} dynamic")
    return stable, dynamic


# ---------------------------------------------------------------------------
# Scroll explore
# ---------------------------------------------------------------------------

def _scroll_explore(
    wda_url: str,
    session_id: str,
    screen_w: int,
    screen_h: int,
    max_pages: int = 3,
    settle_wait: float = 0.6,
    profile_filter=None,
    preserve_set=None,
) -> list[dict]:
    """Dump current screen, scroll to find off-screen elements.

    Tags each element as fixed=True if it appears at the same coordinates
    on >=2 scroll pages (e.g. header tabs, bottom nav bars).
    """
    mid_x = screen_w // 2
    from_y = int(screen_h * 0.7)
    to_y = int(screen_h * 0.2)

    # Collect elements per page (no dedup yet — need per-page data for fixed detection)
    page_elements: list[list[dict]] = []
    for page in range(max_pages + 1):
        time.sleep(settle_wait)
        xml_str = _dump_xml_str(wda_url, session_id)
        if not xml_str:
            break

        elements = _parse_elements_ios(xml_str)
        page_elems = []
        for e in elements:
            if _should_skip(e["text"], profile_filter, preserve_set):
                continue
            # Drop elements whose center is outside the visible screen.
            # WDA may return content-absolute coords for off-screen cells
            # (e.g. y=50135 for a table cell far below the viewport).
            # Filtering here ensures elements are only recorded when their
            # center is actually visible on the current scroll page.
            cx, cy = e["center"]
            if cx < 0 or cy < 0 or cx > screen_w or cy > screen_h:
                continue
            page_elems.append(e)
        page_elements.append(page_elems)

        if page >= max_pages:
            break
        _wda_swipe(mid_x, from_y, mid_x, to_y, wda_url, session_id)
        if len(page_elems) == 0 and page > 0:
            break

    # Detect fixed elements: same (text, x, y) appears on >=2 pages
    from collections import defaultdict
    pos_counts: dict[str, dict[tuple, int]] = defaultdict(lambda: defaultdict(int))
    for page_idx, elems in enumerate(page_elements):
        for e in elems:
            cx = round(e["center"][0])
            cy = round(e["center"][1])
            pos_key = (cx, cy)
            text_key = e["text"].lower().strip()
            pos_counts[text_key][pos_key] += 1

    fixed_texts: set[str] = set()
    for text_key, positions in pos_counts.items():
        for pos_key, count in positions.items():
            if count >= 2:
                fixed_texts.add(text_key)
                break

    # Deduplicate by text, keep first occurrence, tag as fixed or not
    all_elements = []
    seen_texts = set()
    for page_idx, elems in enumerate(page_elements):
        for e in elems:
            key = e["text"].lower().strip()
            if key in seen_texts:
                continue
            seen_texts.add(key)
            e["found_at_scroll"] = page_idx
            e["fixed"] = key in fixed_texts
            all_elements.append(e)

    return all_elements


# ---------------------------------------------------------------------------
# Main build function
# ---------------------------------------------------------------------------

def _extract_json(text: str) -> dict:
    """Extract the first JSON object from LLM response with bracket counting."""
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Fallback: find first { } block with bracket counting
    try:
        start = text.index("{")
        depth = 0
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    return json.loads(text[start:i + 1])
    except (ValueError, json.JSONDecodeError):
        pass
    return {}


def _enrich_map(
    output_data: dict,
    app_name: str,
    api_key: str = "EMPTY",
    api_base: str = "http://localhost:8002/v1",
    model: str = "Qwen/Qwen2.5-3B-Instruct",
):
    """Use LLM to add aliases, semantic types, screen descriptions, and app metadata.

    Modifies *output_data* in-place.  Enrichment is best-effort —
    LLM failures are caught and the map is saved without enrichment.
    """
    from phonecli.llm_client import text_completion
    from phonecli.prompts import (
        ELEMENT_ENRICH_PROMPT, SCREEN_ENRICH_PROMPT, APP_ENRICH_PROMPT,
    )

    screens = output_data.get("screens", [])
    if not screens:
        return

    print("[Enrich] Adding aliases, types, and descriptions...")

    # --- 1. Per-screen: element aliases + semantic types ---
    for screen in screens:
        elements = screen.get("elements", [])
        if not elements:
            continue

        text_list = "\n".join(
            f"{i}: {e['text']}" for i, e in enumerate(elements)
        )
        try:
            rsp = text_completion(
                ELEMENT_ENRICH_PROMPT.format(app_name=app_name, element_list=text_list),
                "Output one JSON object per line.",
                api_key=api_key, api_base=api_base, model=model,
                max_tokens=2048, temperature=0.0,
            )
            # Parse line-by-line JSON
            for line in rsp.strip().splitlines():
                line = line.strip()
                if not line.startswith("{"):
                    continue
                try:
                    item = json.loads(line)
                except json.JSONDecodeError:
                    continue
                orig_text = item.get("text", "")
                aliases = item.get("aliases", [])
                stype = item.get("semantic_type", "")
                for e in elements:
                    if e["text"] == orig_text:
                        if aliases:
                            e.setdefault("aliases", []).extend(
                                a for a in aliases if a not in e.get("aliases", [])
                            )
                        if stype:
                            e["semantic_type"] = stype
                        break
        except Exception as exc:
            print(f"[Enrich] Element enrichment failed for {screen.get('id', '?')}: {exc}")
            continue

    # --- 2. Per-screen: description, scrollable ---
    for screen in screens:
        elements = screen.get("elements", [])
        text_list = "\n".join(e["text"] for e in elements[:30])
        try:
            rsp = text_completion(
                SCREEN_ENRICH_PROMPT.format(
                    app_name=app_name,
                    screen_id=screen.get("id", "?"),
                    element_list=text_list,
                ),
                "Output JSON only.",
                api_key=api_key, api_base=api_base, model=model,
                max_tokens=256, temperature=0.0,
            )
            data = _extract_json(rsp)
            if data.get("description"):
                screen["description"] = data["description"]
            screen["scrollable"] = data.get("scrollable", False)
            screen["scroll_direction"] = data.get("scroll_direction", "")
        except Exception as exc:
            print(f"[Enrich] Screen description failed for {screen.get('id', '?')}: {exc}")
            continue

    # --- 3. App-level metadata ---
    screen_summary_parts = []
    for s in screens:
        desc = s.get("description", "") or f"{len(s.get('elements', []))} elements"
        screen_summary_parts.append(f"  {s['id']}: {desc}")
    screen_summary = "\n".join(screen_summary_parts[:30])

    try:
        rsp = text_completion(
            APP_ENRICH_PROMPT.format(app_name=app_name, screen_summary=screen_summary),
            "Output JSON only.",
            api_key=api_key, api_base=api_base, model=model,
            max_tokens=512, temperature=0.0,
        )
        data = _extract_json(rsp)
        if data.get("launch_behavior"):
            output_data["launch_behavior"] = data["launch_behavior"]
        if data.get("common_tasks"):
            output_data["common_tasks"] = data["common_tasks"]
        if data.get("known_limitations"):
            output_data["known_limitations"] = data["known_limitations"]
        print(f"[Enrich] App metadata: launch={output_data.get('launch_behavior')}, "
              f"tasks={len(output_data.get('common_tasks', []))}")
    except Exception as exc:
        print(f"[Enrich] App metadata enrichment failed: {exc}")

    print("[Enrich] Done.")


# ---------------------------------------------------------------------------
# Checkpoint save / load
# ---------------------------------------------------------------------------

def _save_checkpoint(checkpoint_path: str, **state):
    """Save crawler state as JSON checkpoint."""
    os.makedirs(os.path.dirname(checkpoint_path) or ".", exist_ok=True)
    # Write to temp file then rename (atomic on same filesystem)
    tmp = checkpoint_path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(state, f, ensure_ascii=False, default=str)
    os.replace(tmp, checkpoint_path)


def _load_checkpoint(checkpoint_path: str) -> dict:
    """Load crawler state from JSON checkpoint."""
    if not os.path.exists(checkpoint_path):
        return None
    with open(checkpoint_path, "r") as f:
        data = json.load(f)
    # Restore tuple centers from lists
    for screen in data.get("screens", []):
        for e in screen.get("elements", []):
            if isinstance(e.get("center"), list):
                e["center"] = tuple(e["center"])
    return data


def build_app_map(
    wda_url: str = "http://localhost:8100",
    session_id: str = None,
    bundle_id: str = None,
    app_name: str = "App",
    output_path: str = "app_map.yaml",
    max_screens: int = 50,
    max_depth: int = 3,
    scroll_pages: int = 3,
    redact: bool = True,
    classify: bool = True,
    enrich: bool = True,
    llm_api_key: str = "EMPTY",
    llm_api_base: str = "http://localhost:8002/v1",
    llm_model: str = "Qwen/Qwen2.5-3B-Instruct",
    profile: dict = None,
    checkpoint_path: str = None,
    resume_from: str = None,
) -> str:
    """Crawl an iOS app and generate an app map YAML file.

    If *profile* is provided, its dynamic_patterns filter out obviously
    dynamic content and preserve_navigation prevents filtering of key UI
    elements. LLM classify (if enabled) further labels remaining elements.

    If *checkpoint_path* is set, save progress after each new screen.
    If *resume_from* is set, load checkpoint and continue from saved state.
    """
    if not bundle_id:
        print("Error: --bundle-id is required")
        sys.exit(1)
    if not session_id:
        print("Error: --session-id is required (start a WDA session first)")
        sys.exit(1)

    # Build profile filter if provided
    profile_filter = None
    preserve_set = None
    if profile:
        from phonecli.profile_builder import build_profile_filter
        profile_filter, preserve_set = build_profile_filter(profile)
        dynamic_pats = len(profile.get("dynamic_patterns", []))
        preserved = len(profile.get("preserve_navigation", []))
        print(f"[Build] Using app profile: {dynamic_pats} patterns, {preserved} preserved")

    screen_w, screen_h = _get_screen_size_wda(wda_url, session_id)
    print(f"[Build] Screen: {screen_w}x{screen_h} (logical points)")
    print(f"[Build] App: {app_name} ({bundle_id})")

    # Start keepalive thread (idleTimerDisabled + fallback periodic tap).
    # Thread is daemon=True — dies with the process if we crash mid-build.
    keepalive_stop = _start_keepalive(wda_url, session_id, interval=25)

    # ---- Launch app ----
    launch_full = [
        {"action": "force_stop", "bundle_id": bundle_id, "wait": 1.0},
        {"action": "launch", "bundle_id": bundle_id, "wait": 3.0},
    ]

    def _replay(macro: list):
        """Replay a macro action list. Each step: {action, ..., wait?}."""
        for step in macro:
            action = step.get("action", "")
            if action == "launch":
                _wda_launch(step.get("bundle_id", bundle_id), wda_url, session_id)
            elif action == "tap":
                _wda_tap(step["x"], step["y"], wda_url, session_id)
            elif action == "swipe":
                _wda_swipe(step["x1"], step["y1"], step["x2"], step["y2"],
                           wda_url, session_id)
            elif action == "force_stop":
                _wda_terminate(step.get("bundle_id", bundle_id), wda_url, session_id)
            if "wait" in step:
                time.sleep(step["wait"])

    # ---- Resume from checkpoint ----
    if resume_from:
        ck = _load_checkpoint(resume_from)
        if not ck:
            print(f"Error: checkpoint not found: {resume_from}")
            sys.exit(1)
        print(f"[Build] Resuming from checkpoint: {resume_from}")
        screens = ck["screens"]
        screen_macros = ck["screen_macros"]
        full_paths = ck["full_paths"]
        visited_sigs = ck["visited_sigs"]
        screen_depths = ck["screen_depths"]
        queue = ck["queue"]
        print(f"[Build]   {len(screens)} screens, {len(queue)} in queue")
        # Re-launch to reset app state, then navigate to screen_0
        print("[Build] Re-launching app...")
        _replay(launch_full)
        time.sleep(2.0)
        _replay(full_paths.get("screen_0", launch_full))
        time.sleep(1.0)
    else:
        # ---- Fresh launch + screen_0 ----
        print("[Build] Launching app...")
        _replay(launch_full)
        # Verify launch: poll until we get meaningful elements
        for attempt in range(5):
            test_xml = _dump_xml_str(wda_url, session_id)
            if test_xml:
                test_elems = _parse_elements_ios(test_xml)
                visible = [e for e in test_elems if not _should_skip(e["text"], profile_filter, preserve_set)]
                if len(visible) >= 5:
                    print(f"[Build] App launched, {len(visible)} visible elements")
                    break
            print(f"[Build] Waiting for app to load... (attempt {attempt + 1})")
            time.sleep(1.5)
        else:
            print("[Build] Warning: app may not have loaded correctly")

        # ---- Crawl screen_0 ----
        print("[Build] Crawling screen_0...")
        elements = _scroll_explore(wda_url, session_id, screen_w, screen_h, scroll_pages,
                                   profile_filter=profile_filter,
                                   preserve_set=preserve_set)
        if classify:
            elements, _ = _classify_elements_with_llm(
                elements, app_name, llm_api_key, llm_api_base, llm_model)
        sig = _build_signature(elements, profile_filter=profile_filter,
                               preserve_set=preserve_set)

        screens = [{"id": "screen_0", "elements": elements}]
        screen_macros = {"screen_0": []}
        full_paths = {"screen_0": launch_full}
        visited_sigs = {sig: "screen_0"}
        screen_depths = {"screen_0": 0}
        queue = ["screen_0"]

        print(f"[Build] screen_0: {len(elements)} elements")

        # Save initial checkpoint if enabled
        if checkpoint_path:
            _save_checkpoint(checkpoint_path,
                             screens=screens, screen_macros=screen_macros,
                             full_paths=full_paths, visited_sigs=visited_sigs,
                             screen_depths=screen_depths, queue=queue)

    # ---- BFS ----
    while queue and len(screens) < max_screens:
        from_id = queue.pop(0)
        try:
            from_idx = next(i for i, s in enumerate(screens) if s["id"] == from_id)
        except StopIteration:
            print(f"[Build]   WARNING: {from_id} not found in screens — skipping")
            continue
        from_screen = screens[from_idx]
        from_depth = screen_depths[from_id]

        if from_depth >= max_depth:
            continue

        for elem in from_screen["elements"]:
            if _should_skip(elem["text"], profile_filter, preserve_set):
                continue
            if elem.get("leads_to"):
                continue
            if len(screens) >= max_screens:
                break

            # Navigate to from_screen via FULL path replay
            print(f"[Build]   navigating to {from_id}...")
            _replay(full_paths[from_id])
            time.sleep(1.0)

            # Scroll to element's found_at_scroll position before tapping
            scroll_needed = elem.get("found_at_scroll", 0)
            if scroll_needed > 0:
                mid_x = screen_w // 2
                sy1 = int(screen_h * 0.7)
                sy2 = int(screen_h * 0.2)
                for _ in range(scroll_needed):
                    _wda_swipe(mid_x, sy1, mid_x, sy2, wda_url, session_id)
                    time.sleep(0.5)
                time.sleep(0.4)  # settle after final scroll before tap

            # Tap element
            x, y = elem["center"]
            label = elem["text"][:40]
            print(f"[Build]   tap ({x},{y}) \"{label}\"" +
                  (f" (scrolled {scroll_needed})" if scroll_needed > 0 else ""))
            _wda_tap(x, y, wda_url, session_id)
            time.sleep(1.5)

            # Dump new screen
            new_elements = _scroll_explore(wda_url, session_id, screen_w, screen_h,
                                           scroll_pages, profile_filter=profile_filter,
                                           preserve_set=preserve_set)
            if not new_elements:
                print(f"[Build]   → empty, skip")
                continue

            if classify:
                new_elements, _ = _classify_elements_with_llm(
                    new_elements, app_name, llm_api_key, llm_api_base, llm_model)
                if not new_elements:
                    print(f"[Build]   → no stable elements, skip")
                    continue

            new_sig = _build_signature(new_elements, profile_filter=profile_filter,
                                       preserve_set=preserve_set)

            # Same screen?
            if new_sig == _build_signature(from_screen["elements"],
                                           profile_filter=profile_filter,
                                           preserve_set=preserve_set):
                continue

            # Already visited?
            if new_sig in visited_sigs:
                existing_id = visited_sigs[new_sig]
                elem["leads_to"] = existing_id
                print(f"[Build]   → {existing_id} (visited)")
                continue

            # New screen
            new_id = f"screen_{len(screens)}"
            new_depth = from_depth + 1
            elem["leads_to"] = new_id

            # Relative macro: just the tap from parent
            rel_macro = [{"action": "tap", "x": x, "y": y, "wait": 1.0}]
            screen_macros[new_id] = rel_macro
            # Full path: parent's full path + this tap
            full_paths[new_id] = full_paths[from_id] + rel_macro

            screens.append({"id": new_id, "elements": new_elements})
            visited_sigs[new_sig] = new_id
            screen_depths[new_id] = new_depth
            queue.append(new_id)

            print(f"[Build]   → {new_id} (depth {new_depth}, {len(new_elements)} el)")

            # Save checkpoint after each new screen
            if checkpoint_path:
                _save_checkpoint(checkpoint_path,
                                 screens=screens, screen_macros=screen_macros,
                                 full_paths=full_paths, visited_sigs=visited_sigs,
                                 screen_depths=screen_depths, queue=queue)

    # Stop keepalive
    keepalive_stop.set()

    # Redact PII before output
    if redact:
        screens = _redact_screens(screens)

    # ---- Build YAML ----
    output_screens = []
    for screen in screens:
        out_elems = []
        for e in screen["elements"]:
            rx = round(e["center"][0] / screen_w, 4)
            ry = round(e["center"][1] / screen_h, 4)
            out_elem = {
                "text": e["text"],
                "center": [rx, ry],
                "found_at_scroll": e.get("found_at_scroll", 0),
                "fixed": e.get("fixed", False),
            }
            if e.get("leads_to"):
                out_elem["leads_to"] = e["leads_to"]
            out_elems.append(out_elem)
        output_screens.append({"id": screen["id"], "elements": out_elems})

    # Store FULL paths for every screen (not relative from parent).
    # This way build_operations in app_map.py works without prefix accumulation.
    output_macros = {"screen_0": launch_full}
    for sid, rel_macro in screen_macros.items():
        if sid != "screen_0":
            output_macros[sid] = full_paths[sid]

    output_data = {
        "app": app_name,
        "package": bundle_id,
        "screen_w": screen_w,
        "screen_h": screen_h,
        "screens": output_screens,
        "screen_macros": output_macros,
    }

    # ---- Optional: LLM enrichment (aliases, descriptions, app metadata) ----
    if enrich:
        try:
            _enrich_map(output_data, app_name,
                        api_key=llm_api_key, api_base=llm_api_base, model=llm_model)
        except Exception as e:
            print(f"[Build] Enrichment failed ({e}) — saving map without enrichment.")

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w") as f:
        yaml.dump(output_data, f, default_flow_style=False, allow_unicode=True,
                  sort_keys=False)

    # Remove checkpoint only after successful yaml.dump
    if checkpoint_path and os.path.exists(checkpoint_path):
        os.remove(checkpoint_path)
        print(f"[Build] Checkpoint removed: {checkpoint_path}")

    total_el = sum(len(s["elements"]) for s in screens)
    total_edges = sum(1 for s in screens for e in s["elements"] if e.get("leads_to"))
    print(f"\n[Build] Done: {output_path}")
    print(f"[Build] Screens: {len(screens)}  Elements: {total_el}  Edges: {total_edges}")
    flags = []
    if classify:
        flags.append("classify")
    if enrich:
        flags.append("enrich")
    if flags:
        print(f"[Build] LLM features: {', '.join(flags)}")

    return output_path
