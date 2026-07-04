"""Stage 5: Map sanitization — classify and replace personal data.

Two modes:
  - LLM mode (default): heuristic scan → LLM classifies with screen context
  - Rule mode (fallback): pattern-based classification for offline/reliability

Algorithm:
  1. Deterministic pass: email, phone, bundle ID → immediate replacement
  2. Candidate scan: collect all texts that COULD be personal data
  3. LLM classify: send candidates + screen context → get categories
  4. Global replace: substitute all classified texts across ALL screens
"""

import json
import os
import re
import time

import yaml

from phonecli.prompts import SANITIZE_CLASSIFY_PROMPT


# ---------------------------------------------------------------------------
# Deterministic patterns (always-on, no LLM needed)
# ---------------------------------------------------------------------------

_BUNDLE_ID_RE = re.compile(r'^[a-zA-Z][\w-]*\.[a-zA-Z][\w-]*(\.[a-zA-Z][\w-]*)+$')
_PHONE_RE = re.compile(r'\+?\d[\d\s\xa0\-]{7,}')
_EMAIL_RE = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')

# Texts that are definitely system UI, never personal data
_KNOWN_SYSTEM = {
    # English
    'settings', 'general', 'wi-fi', 'bluetooth', 'cellular', 'battery',
    'vpn', 'camera', 'control center', 'notifications', 'wallpaper',
    'focus', 'screen time', 'privacy', 'security', 'accessibility',
    'developer', 'apps', 'icloud', 'game center', 'airdrop', 'siri',
    'standby', 'passcode', 'emergency sos', 'hotspot', 'facetime',
    'messages', 'safari', 'mail', 'music', 'photos', 'calendar',
    'maps', 'wallet', 'health', 'home', 'news', 'stocks', 'weather',
    'notes', 'reminders', 'files', 'shortcuts', 'translate',
    'app store', 'apple account', 'family', 'personal hotspot',
    'display', 'brightness', 'home screen', 'app library',
    'sound', 'haptics', 'face id', 'action button',
    'apple intelligence', 'sign-in', 'sign in', 'sign out',
    'subscriptions', 'purchase sharing', 'location sharing',
    'find my', 'media', 'sign in with apple',
    'iphone storage', 'find my iphone', 'apple watch app',
    'transfer or reset iphone', 'erase this iphone',
    # Chinese
    '搜索', '设置', '通知', '照片', '相机', '日历', '时钟',
    '地图', '天气', '音乐', '钱包', '健康', '文件', '密码',
    '显示', '亮度', '声音', '通用', '隐私', '安全', '还原',
    '传输', '蓝牙', '键盘', '字体', '语言', '日期', '时间',
    '返回', '取消', '确认', '完成', '关于', '隔空投送',
    '屏幕使用时间', '触控', '面容', '主屏幕', '控制中心',
    '勿扰模式', '个人热点', '软件更新', '蜂窝网络', '无线局域网',
    '电池', '存储', '后台', '隔空', '面容', '家人共享',
    # Keyboard/input
    '简体中文', '繁体中文', '英文', '拼音', '手写', '笔画',
}
_KNOWN_SYSTEM_LOWER = {t.lower() for t in _KNOWN_SYSTEM}

# Category → placeholder mapping
_CATEGORY_PLACEHOLDER = {
    'name': '[Name]',
    'email': '[Email]',
    'phone': '[Phone]',
    'device': '[Device]',
    'app': '[App]',
    'region': '[Region]',
    'account': '[Account]',
}


# ---------------------------------------------------------------------------
# Deterministic pass
# ---------------------------------------------------------------------------

def _deterministic_replace(text: str) -> str:
    """Return placeholder if text matches a deterministic pattern, else empty."""
    t = text.strip()
    if _EMAIL_RE.search(t):
        return '[Email]'
    if _PHONE_RE.search(t) and len(re.sub(r'[^\d]', '', t)) >= 7:
        return '[Phone]'
    if _BUNDLE_ID_RE.match(t):
        return '[App]'
    return ''


# ---------------------------------------------------------------------------
# Candidate scan: collect texts that COULD be personal data
# ---------------------------------------------------------------------------

def _is_candidate(text: str) -> bool:
    """Heuristic: could this text be personal data worth LLM review?

    Broad filter — errs on the side of inclusion. The LLM does final classification.
    """
    t = text.strip()
    if not t or len(t) < 2:
        return False
    if t.lower() in _KNOWN_SYSTEM_LOWER:
        return False
    # Already caught by deterministic pass
    if _deterministic_replace(t):
        return False
    # Placeholder from previous redaction
    if t.startswith('[') and t.endswith(']'):
        return False

    # Any non-ASCII (Chinese, emoji, special chars) → candidate
    if any(ord(c) > 127 for c in t):
        return True

    # CamelCase with internal capitals (e.g. "MacBook", "McDonald's") → candidate
    if re.match(r"^[A-Z][a-zA-Z]+(\s+[A-Z][a-zA-Z]+)*$", t) and len(t) > 5:
        return True
    if "'" in t and not t.lower().startswith(("don'", "can'", "won'", "isn'", "aren'", "doesn'", "didn'", "hasn'", "wasn'", "weren'")):
        return True

    # Contains digits (could be count, date, model number) → candidate
    if any(c.isdigit() for c in t):
        return True

    return False


def _extract_candidates(screens: list) -> dict:
    """Scan map, collect texts that might be personal data.

    Returns: {text: [screen_descriptions]} for unique candidate texts.
    """
    candidates = {}
    for s in screens:
        desc = s.get("description", "") or s["id"]
        for e in s.get("elements", []):
            t = e.get("text", "").strip()
            if not _is_candidate(t):
                continue
            if t not in candidates:
                candidates[t] = []
            if desc not in candidates[t]:
                candidates[t].append(desc)
    return candidates


# ---------------------------------------------------------------------------
# LLM classification
# ---------------------------------------------------------------------------

def _parse_llm_response(rsp: str) -> dict:
    """Parse LLM JSON response, returning dict or empty dict on failure."""
    try:
        data = json.loads(rsp.strip())
    except json.JSONDecodeError:
        start = rsp.find("{")
        end = rsp.rfind("}") + 1
        if start >= 0 and end > start:
            data = json.loads(rsp[start:end])
        else:
            return {}
    if not isinstance(data, dict):
        return {}
    return data


def _llm_classify(
    candidates: dict,
    app_name: str,
    api_key: str = "EMPTY",
    api_base: str = "http://localhost:8002/v1",
    model: str = "Qwen/Qwen2.5-3B-Instruct",
    batch_size: int = 150,
) -> dict:
    """Send candidates to LLM in batches for classification.

    Args:
        candidates: {text: [screen_descriptions]}
        batch_size: max items per LLM call (default 150).
    Returns:
        {text: placeholder} for texts classified as personal data.
    """
    if not candidates:
        return {}

    from phonecli.llm_client import text_completion

    # Build sorted item list with screen context
    items = []
    for text, screens in sorted(candidates.items()):
        ctx = ", ".join(screens[:3])
        items.append(f"  \"{text}\"  [screens: {ctx}]")
    total = len(items)

    # Split into batches
    batches = [items[i:i + batch_size] for i in range(0, len(items), batch_size)]
    num_batches = len(batches)

    all_replacements = {}
    total_replace = 0
    total_skip = 0

    for batch_idx, batch_items in enumerate(batches):
        element_list = "\n".join(batch_items)
        system_prompt = SANITIZE_CLASSIFY_PROMPT.format(
            app_name=app_name, element_list=element_list)

        label = f"batch {batch_idx + 1}/{num_batches}"
        print(f"[Sanitize] Sending {len(batch_items)} candidates to LLM ({label})...")
        time.sleep(0.5)
        rsp = text_completion(system_prompt, "Output the JSON classification.",
                              api_key=api_key, api_base=api_base, model=model,
                              max_tokens=4096, temperature=0.0)

        data = _parse_llm_response(rsp)
        if not data:
            print(f"[Sanitize] {label}: LLM response not valid JSON, skipping batch")
            continue

        batch_replace = 0
        batch_skip = 0
        for text, category in data.items():
            category = category.lower().strip()
            if category == 'skip':
                batch_skip += 1
                continue
            placeholder = _CATEGORY_PLACEHOLDER.get(category)
            if placeholder:
                all_replacements[text] = placeholder
                batch_replace += 1

        total_replace += batch_replace
        total_skip += batch_skip
        print(f"[Sanitize] {label}: {batch_replace} replace, {batch_skip} skip")

    print(f"[Sanitize] LLM classified: {total_replace} replace, {total_skip} skip "
          f"(across {num_batches} batches, {total} total)")
    return all_replacements


# ---------------------------------------------------------------------------
# Rule-based classification (fallback mode)
# ---------------------------------------------------------------------------

def _rule_classify(candidates: dict, screens: list) -> dict:
    """Simple rule-based classification as fallback when LLM is unavailable."""
    replacements = {}
    for text, _screen_descs in candidates.items():
        # Try to infer category from text patterns
        if re.match(r'^\+?\d[\d\s\xa0\-]{7,}$', text.strip()):
            replacements[text] = '[Phone]'
        elif _BUNDLE_ID_RE.match(text.strip()):
            replacements[text] = '[App]'
        elif any(ord(c) > 127 for c in text):
            # Has non-ASCII → likely Chinese name/app/region
            chinese = [c for c in text if '一' <= c <= '鿿']
            if 2 <= len(chinese) <= 3:
                replacements[text] = '[Name]'
            elif 4 <= len(chinese) <= 8:
                replacements[text] = '[App]'
    return replacements


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def sanitize_map(
    map_path: str,
    output_path: str = None,
    use_llm: bool = True,
    llm_api_key: str = "EMPTY",
    llm_api_base: str = "http://localhost:8002/v1",
    llm_model: str = "Qwen/Qwen2.5-3B-Instruct",
) -> dict:
    """Load map, detect and replace personal data, save sanitized version.

    Args:
        map_path: Path to the app map YAML.
        output_path: Output path (default: overwrite map_path).
        use_llm: Use LLM for classification (recommended). Falls back to rules on error.
        llm_api_key/base/model: LLM config for classification.

    Returns:
        dict with keys: path, replaced, replacements
    """
    if not os.path.exists(map_path):
        raise FileNotFoundError(f"Map not found: {map_path}")

    with open(map_path, "r") as f:
        data = yaml.safe_load(f)

    screens = data.get("screens", [])
    app_name = data.get("app", "App")
    if not screens:
        return {"path": map_path, "replaced": 0, "replacements": []}

    to_replace = {}

    # --- Pass 1: Deterministic (email, phone, bundle ID) ---
    det_count = 0
    for s in screens:
        for e in s.get("elements", []):
            t = e.get("text", "").strip()
            placeholder = _deterministic_replace(t)
            if placeholder and t not in to_replace:
                to_replace[t] = placeholder
                det_count += 1
    if det_count:
        print(f"[Sanitize] Deterministic pass: {det_count} items")

    # --- Pass 2: Heuristic scan for candidates ---
    candidates = _extract_candidates(screens)
    print(f"[Sanitize] Candidate scan: {len(candidates)} items for review")

    # --- Pass 3: Classification (LLM or rule fallback) ---
    classified = {}
    if use_llm:
        try:
            classified = _llm_classify(
                candidates, app_name,
                api_key=llm_api_key, api_base=llm_api_base, model=llm_model)
        except Exception as e:
            print(f"[Sanitize] LLM classification failed ({e}), trying rule fallback")
            classified = _rule_classify(candidates, screens)
    else:
        classified = _rule_classify(candidates, screens)

    # Merge classified into to_replace (classified takes priority)
    for text, placeholder in classified.items():
        to_replace[text] = placeholder
    print(f"[Sanitize] Total items to replace: {len(to_replace)}")

    # --- Pass 4: Global replace across ALL screens ---
    replaced_count = 0
    for s in screens:
        for e in s.get("elements", []):
            old_text = e.get("text", "")
            if old_text in to_replace:
                e["text"] = to_replace[old_text]
                replaced_count += 1

    print(f"[Sanitize] Replaced {replaced_count} occurrences across all screens")

    # --- Save ---
    output_path = output_path or map_path
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True,
                  sort_keys=False)

    print(f"[Sanitize] Saved: {output_path}")

    replacements = [(old, new) for old, new in sorted(to_replace.items())]
    return {"path": output_path, "replaced": replaced_count,
            "replacements": replacements}
