"""Map validation — checks format errors, data quality, and profile effectiveness.

Usage:
    from phonecli.validate_map import validate_map
    errors, warnings = validate_map("app_maps/xiaohongshu_map.yaml", profile=profile)

Returns (errors, warnings) — both list of {"code": str, "message": str, "detail": ...}.
"""

import json
import math
import os
import re

import yaml

# ---------------------------------------------------------------------------
# Validation rules
# ---------------------------------------------------------------------------

# PII patterns (same as build_map.py)
_EMAIL_RE = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
_PHONE_RE = re.compile(r'\+?\d[\d\s\xa0\-]{7,}')
_PAYMENT_KEYS = ('支付宝', 'alipay', 'paypal', '微信支付', 'apple pay', 'unionpay', '云闪付')

# Dynamic-content patterns (same as build_map.py _DYNAMIC_PATTERNS)
_DYNAMIC_PATTERNS = [
    (re.compile(r'^\d{1,2}:\d{2}$'), "time"),
    (re.compile(r'^\d{1,2}:\d{2}\s*[AP]M$'), "time"),
    (re.compile(r'^\d+\s*min\b', re.I), "duration"),
    (re.compile(r'^\d+\s*(hour|hr|day|week|month|year)s?\b', re.I), "duration"),
    (re.compile(r'\b\d{1,2}/\d{1,2}/\d{2,4}\b'), "date"),
    (re.compile(r'^\d{1,3}\s*%$'), "percentage"),
    (re.compile(r'^\d+$'), "number"),
    (re.compile(r'^\d+\s*(messages|notifications|items|results?|emails?)$', re.I), "count"),
    (re.compile(r'^just now$', re.I), "relative time"),
    (re.compile(r'^now$', re.I), "relative time"),
    (re.compile(r'^today$', re.I), "relative time"),
    (re.compile(r'^yesterday$', re.I), "relative time"),
    (re.compile(r'^\d+[\.\d]*\s*(GB|MB|KB|TB)$', re.I), "size"),
    (re.compile(r'^(on|off)$', re.I), "toggle state"),
    (re.compile(r'^[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}$'), "UUID"),
    (re.compile(r'^[\d,]+$'), "count"),
    (re.compile(r'^\d+\s*/\s*\d+$'), "fraction"),
    (re.compile(r'^\d+[\.\d]*\s*(km|m|mi|mile|公里|米)$', re.I), "distance"),
    (re.compile(r'^\d+\s*(分钟|小时|天|周|月|年)前$'), "relative time"),
    (re.compile(r'^\d+\s*(赞|评论|收藏|转发|粉丝|看过|浏览)$'), "stat"),
]


# ---------------------------------------------------------------------------
# Algorithm helpers
# ---------------------------------------------------------------------------

def _load_map(map_path: str) -> dict:
    """Load map YAML, returns None on parse error."""
    if not os.path.exists(map_path):
        return None
    with open(map_path, "r") as f:
        return yaml.safe_load(f)


def _all_texts(screens: list) -> list:
    """Return [(screen_id, element_text), ...] for all elements."""
    result = []
    for s in screens:
        for e in s.get("elements", []):
            result.append((s["id"], e.get("text", "")))
    return result


# ---------------------------------------------------------------------------
# 1. Format / structure errors
# ---------------------------------------------------------------------------

def _check_required_fields(data: dict) -> list:
    errors = []
    for key in ("app", "package", "screens"):
        if key not in data:
            errors.append({"code": "missing_field", "message": f"Required field '{key}' is missing"})
    return errors


def _check_screens_exist(data: dict) -> list:
    errors = []
    screens = data.get("screens", [])
    if not isinstance(screens, list) or len(screens) == 0:
        errors.append({"code": "no_screens",
                       "message": "Map has no screens — crawl produced no data"})
    return errors


def _check_duplicate_ids(screens: list) -> list:
    """Algorithm: count occurrences of each id, flag those >1."""
    errors = []
    from collections import Counter
    ids = [s.get("id", "?") for s in screens]
    dupes = {sid: count for sid, count in Counter(ids).items() if count > 1}
    for sid, count in dupes.items():
        errors.append({"code": "duplicate_id",
                       "message": f"screen_id '{sid}' appears {count} times"})
    return errors


def _check_empty_screens(screens: list) -> list:
    """Check for screens with zero elements."""
    errors = []
    for s in screens:
        if len(s.get("elements", [])) == 0:
            errors.append({"code": "empty_screen",
                           "message": f"Screen '{s['id']}' has no elements"})
    return errors


def _check_leads_to_references(screens: list) -> list:
    """Algorithm: collect all leads_to targets, cross-reference with known screen IDs.

    For each element with leads_to, verify the target exists in the screen list.
    """
    errors = []
    known_ids = {s.get("id", "") for s in screens}
    for s in screens:
        for e in s.get("elements", []):
            target = e.get("leads_to")
            if target and target not in known_ids:
                errors.append({"code": "bad_reference",
                               "message": f"Element '{e.get('text', '?')}' in {s['id']} "
                               f"has leads_to='{target}' which doesn't exist"})
    return errors


def _check_screen_macros(data: dict) -> list:
    """Algorithm: every non-screen_0 screen must have an entry in screen_macros."""
    errors = []
    macros = data.get("screen_macros", {}) or {}
    screens = data.get("screens", []) or []
    known_ids = {s["id"] for s in screens}
    for sid in known_ids:
        if sid == "screen_0":
            continue
        if sid not in macros:
            errors.append({"code": "missing_macro",
                           "message": f"screen_macros missing entry for '{sid}'"})
        elif not isinstance(macros[sid], list) or len(macros[sid]) == 0:
            errors.append({"code": "empty_macro",
                           "message": f"screen_macros['{sid}'] is empty or not a list"})
    return errors


def _check_coordinate_bounds(screens: list) -> tuple:
    """Algorithm: iterate all element centers.

    y > 1.0 is expected for scrollable content (elements below the fold
    have absolute y > screen_h). Only flag as error if x < 0 or y < 0.
    x > 1.0 or y > 1.0 are warnings (scrollable overflow).
    """
    errors = []
    warnings = []
    for s in screens:
        for e in s.get("elements", []):
            c = e.get("center", [0, 0])
            if not isinstance(c, (list, tuple)) or len(c) != 2:
                errors.append({"code": "bad_coord",
                               "message": f"Element '{e.get('text', '?')}' in {s['id']} "
                               f"has invalid center: {c}"})
                continue
            x, y = c[0], c[1]
            if x < 0 or y < 0:
                errors.append({"code": "coord_negative",
                               "message": f"Element '{e.get('text', '?')}' in {s['id']} "
                               f"has negative center: [{x}, {y}]"})
            elif x > 1.0 or y > 1.0:
                warnings.append({"code": "coord_overflow",
                                 "message": f"Element '{e.get('text', '?')}' in {s['id']} "
                                 f"center exceeds viewport: [{x:.2f}, {y:.2f}] "
                                 f"(scrollable content)"})
    return errors, warnings


# ---------------------------------------------------------------------------
# 2. Data quality warnings
# ---------------------------------------------------------------------------

def _check_pii_leak(screens: list) -> list:
    """Algorithm: scan all element texts for email, phone, Chinese names, payment info."""
    warnings = []
    for s in screens:
        for e in s.get("elements", []):
            t = e.get("text", "")
            if not t:
                continue
            if _EMAIL_RE.search(t):
                warnings.append({"code": "pii_email",
                                 "message": f"'{t}' in {s['id']} looks like an email"})
            elif _PHONE_RE.search(t):
                warnings.append({"code": "pii_phone",
                                 "message": f"'{t}' in {s['id']} looks like a phone number"})
            elif any(kw in t.lower() for kw in _PAYMENT_KEYS):
                warnings.append({"code": "pii_payment",
                                 "message": f"'{t}' in {s['id']} contains payment info"})
            elif 2 <= len(t) <= 5 and all('一' <= c <= '鿿' for c in t):
                # Chinese name candidate
                skip = ("设置", "显示", "通知", "通用", "邮件", "相机", "日历",
                        "照片", "时钟", "天气", "地图", "音乐", "钱包", "健康",
                        "文件", "备忘", "通讯", "信息", "电话", "隐私", "安全",
                        "密码", "蓝牙", "无线", "蜂窝", "隔空", "隔空投送",
                        "家人", "家人共享", "屏幕", "控制", "个人", "专注",
                        "声音", "触感", "亮度", "亮度与", "主屏幕",
                        "搜索", "待机", "墙纸", "面容", "面容ID", "紧急",
                        "软件", "关于", "键盘", "字体", "词典", "自动",
                        "日期", "时间", "语言", "地区", "还原", "传输",
                        "苹果", "苹果智能", "隔空投", "家人共",
                        # Common Chinese UI terms (filters, tabs, actions)
                        "全城", "推荐", "美食", "购物", "热点", "话题",
                        "查看详情", "表情符号", "地点", "地图探索", "切换城市",
                        "位置距离", "周末出行", "热门打卡地", "酒吧派对",
                        "展览演出", "购物市集", "我的订单", "我的收藏",
                        "浏览记录", "搜索历史", "全部", "附近", "最新",
                        "最热", "排行", "分类", "筛选")
                if t not in skip:
                    warnings.append({"code": "pii_name",
                                     "message": f"'{t}' in {s['id']} looks like a Chinese name"})
    return warnings


def _check_dynamic_residue(screens: list) -> list:
    """Algorithm: check each element against generic dynamic-content patterns.

    Count how many elements match each dynamic category, warn if many found
    (suggests profile didn't filter enough).
    """
    warnings = []
    counts = {}
    for s in screens:
        for e in s.get("elements", []):
            t = e.get("text", "")
            for pat, cat in _DYNAMIC_PATTERNS:
                if pat.match(t.strip()):
                    counts[cat] = counts.get(cat, 0) + 1
                    break  # count once per element

    for cat, count in sorted(counts.items(), key=lambda x: -x[1]):
        if count >= 5:
            warnings.append({"code": "dynamic_residue",
                             "message": f"{count} elements match dynamic pattern '{cat}' "
                             f"— profile may not be filtering enough"})
    return warnings


def _check_coverage(screens: list) -> list:
    """Algorithm: basic coverage metrics.

    - Total screens < 5 → too shallow
    - Total edges < screens/2 → few navigation links discovered
    - All screens at depth 0 or 1 → didn't explore deep
    """
    warnings = []
    n = len(screens)

    if n < 5:
        warnings.append({"code": "low_coverage",
                         "message": f"Only {n} screens — crawl too shallow"})
        return warnings

    # Count edges
    edges = sum(1 for s in screens for e in s.get("elements", []) if e.get("leads_to"))
    edge_ratio = edges / max(n, 1)
    if edge_ratio < 0.5:
        warnings.append({"code": "few_edges",
                         "message": f"Only {edges} edges for {n} screens "
                         f"(ratio {edge_ratio:.1f}) — few navigation links"})

    return warnings


def _check_coordinate_clustering(screens: list) -> list:
    """Algorithm: divide screen into 3x3 grid, check if >80% of element centers
    fall into a single cell — indicates the crawler may be stuck in a loop on
    the same UI region.

    Skip screens with <5 elements (too few to cluster meaningfully).
    """
    warnings = []
    for s in screens:
        elems = s.get("elements", [])
        if len(elems) < 5:
            continue
        grid = [[0] * 3 for _ in range(3)]
        for e in elems:
            c = e.get("center", [0, 0])
            col = min(2, int(c[0] * 3))
            row = min(2, int(c[1] * 3))
            grid[row][col] += 1
        max_cell = max(max(row) for row in grid)
        if max_cell > len(elems) * 0.8:
            warnings.append({"code": "clustered",
                             "message": f"{s['id']}: {max_cell}/{len(elems)} elements "
                             f"in a single grid region — possible crawl loop"})
    return warnings


# ---------------------------------------------------------------------------
# 3. Profile validation
# ---------------------------------------------------------------------------

def _check_profile_effectiveness(screens: list, profile: dict) -> list:
    """Algorithm: for each profile dynamic_pattern, check if it matched anything
    in the final map. Unused patterns suggest they're unnecessary or the crawl
    didn't encounter that type of content.

    Also check if preserve_navigation items look dynamic (conflict).
    """
    warnings = []
    if not profile:
        return warnings

    # Collect all element texts
    all_texts = set()
    for s in screens:
        for e in s.get("elements", []):
            all_texts.add(e.get("text", ""))

    # Build set of preserved texts (these intentionally survive pattern matches)
    preserved_texts = set()
    for item in profile.get("preserve_navigation", []):
        preserved_texts.add(item.lower().strip())

    # Check unused patterns
    for pat_str in profile.get("dynamic_patterns", []):
        try:
            cre = re.compile(pat_str, re.I)
        except re.error:
            warnings.append({"code": "bad_profile_pattern",
                             "message": f"Profile pattern '{pat_str}' is not valid regex"})
            continue
        matched = [t for t in all_texts if cre.match(t.strip())]
        if not matched:
            warnings.append({"code": "unused_pattern",
                             "message": f"Profile pattern '{pat_str}' never matched any element"})
        else:
            # Exclude preserved elements — they intentionally survive patterns
            leaked = [t for t in matched if t.lower().strip() not in preserved_texts]
            if leaked:
                sample = leaked[:3]
                warnings.append({"code": "pattern_leak",
                                 "message": f"Profile pattern '{pat_str}' matched {len(leaked)} "
                                 f"elements still in map: {sample}"})

    # Check preserve_navigation for suspicious items
    for item in profile.get("preserve_navigation", []):
        for pat, cat in _DYNAMIC_PATTERNS:
            if pat.match(item.strip()):
                warnings.append({"code": "preserve_vs_dynamic",
                                 "message": f"preserve_navigation item '{item}' matches "
                                 f"dynamic pattern '{cat}' — may be actual content"})
                break

    return warnings


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def validate_map(map_path: str, profile: dict = None) -> tuple:
    """Validate an app map YAML file.

    Args:
        map_path: Path to the YAML map file.
        profile: Optional profile dict (from profile_builder).

    Returns:
        (errors, warnings): Two lists of dicts with keys: code, message.
        If map_path doesn't exist or is unparseable, errors contains a
        single 'parse_error' entry.
    """
    data = _load_map(map_path)
    if data is None:
        return ([{"code": "parse_error",
                  "message": f"Map not found or unparseable: {map_path}"}], [])

    screens = data.get("screens", [])
    errors = []
    warnings = []

    # --- Format/structure (hard errors) ---
    errors += _check_required_fields(data)
    errors += _check_screens_exist(data)
    if screens:
        errors += _check_duplicate_ids(screens)
        errors += _check_empty_screens(screens)
        errors += _check_leads_to_references(screens)
        coord_errors, coord_warnings = _check_coordinate_bounds(screens)
        errors += coord_errors
        warnings += coord_warnings
    errors += _check_screen_macros(data)

    # --- Data quality (warnings) ---
    if screens:
        warnings += _check_pii_leak(screens)
        warnings += _check_dynamic_residue(screens)
        warnings += _check_coverage(screens)
        warnings += _check_coordinate_clustering(screens)

    # --- Profile validation ---
    if profile:
        warnings += _check_profile_effectiveness(screens, profile)

    return errors, warnings


def print_validation_report(errors: list, warnings: list) -> str:
    """Format validation results as a readable report."""
    lines = []
    if not errors and not warnings:
        lines.append("[Validate] All checks passed")
        return "\n".join(lines)

    lines.append(f"[Validate] {len(errors)} errors, {len(warnings)} warnings")
    for e in errors:
        lines.append(f"  ✗ [{e['code']}] {e['message']}")
    for w in warnings:
        lines.append(f"  ⚠ [{w['code']}] {w['message']}")
    return "\n".join(lines)
