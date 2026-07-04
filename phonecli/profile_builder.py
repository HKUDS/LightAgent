"""App-specific profile builder for map crawling.

Three-stage pipeline:
  1. sample: quick crawl of screen_0, collect all visible element texts (~1 min)
  2. profile: LLM generates app-specific dynamic_patterns + preserve_navigation
  3. build: full crawl uses profile to filter out dynamic content

Profile YAML format:
  app: 小红书
  bundle_id: com.xingin.discover
  dynamic_patterns:
    - '^[0-9A-F]{8}-...{12}$'     # UUIDs
    - '^[\d,]+$'                    # counts
  preserve_navigation:
    - "关注"  # tab, not dynamic
    - "发现"  # tab
"""

import json
import os
import re
import time
from typing import Optional

import yaml


# ---------------------------------------------------------------------------
# Profile loading / saving
# ---------------------------------------------------------------------------

def load_profile(profile_path: str) -> Optional[dict]:
    """Load an app profile from YAML. Returns None if not found or invalid."""
    if not profile_path or not os.path.exists(profile_path):
        return None
    try:
        with open(profile_path, "r") as f:
            data = yaml.safe_load(f)
        if not isinstance(data, dict):
            return None
        # Normalize: ensure expected keys exist
        data.setdefault("dynamic_patterns", [])
        data.setdefault("preserve_navigation", [])
        return data
    except Exception:
        return None


def save_profile(profile: dict, output_path: str):
    """Save profile as YAML."""
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w") as f:
        yaml.dump(profile, f, default_flow_style=False, allow_unicode=True,
                  sort_keys=False)


# ---------------------------------------------------------------------------
# Profile-based element filtering
# ---------------------------------------------------------------------------

def build_profile_filter(profile: dict):
    """Build filter components from a profile dict.

    Returns (match_fn, preserve_set) where:
      - match_fn(text) -> True if text matches a dynamic_pattern (should skip)
      - preserve_set: lowercased texts that must NEVER be skipped
    """
    patterns = profile.get("dynamic_patterns", [])
    preserve = set(p.lower().strip() for p in profile.get("preserve_navigation", []))
    compiled = [re.compile(p, re.IGNORECASE) for p in patterns]

    def _match(text: str) -> bool:
        for cre in compiled:
            if cre.match(text.strip()):
                return True
        return False

    return _match, preserve


# ---------------------------------------------------------------------------
# Stage 1: sample screen_0
# ---------------------------------------------------------------------------

def sample_screen0(
    wda_url: str,
    session_id: str,
    bundle_id: str,
    scroll_pages: int = 3,
) -> list[str]:
    """Launch app, collect all visible element texts from screen_0.

    Returns list of element texts (raw, no filtering).
    """
    from phonecli.build_map import (
        _wda_launch, _wda_terminate, _wda_swipe,
        _dump_xml_str, _parse_elements_ios,
        _start_keepalive, _get_screen_size_wda,
        SKIP_TEXTS,
    )

    screen_w, screen_h = _get_screen_size_wda(wda_url, session_id)
    keepalive_stop = _start_keepalive(wda_url, session_id, interval=30)
    try:
        # Launch
        _wda_terminate(bundle_id, wda_url, session_id)
        time.sleep(1.0)
        _wda_launch(bundle_id, wda_url, session_id)
        time.sleep(3.0)

        # Verify launch
        for attempt in range(5):
            test_xml = _dump_xml_str(wda_url, session_id)
            if test_xml and len(_parse_elements_ios(test_xml)) >= 5:
                break
            print(f"[Sample] Waiting for app to load... (attempt {attempt + 1})")
            time.sleep(1.5)

        # Scroll-explore to find all elements (no filtering)
        mid_x = screen_w // 2
        from_y = int(screen_h * 0.7)
        to_y = int(screen_h * 0.2)

        all_texts = []
        seen = set()
        for page in range(scroll_pages + 1):
            time.sleep(0.6)
            xml_str = _dump_xml_str(wda_url, session_id)
            if not xml_str:
                break
            for e in _parse_elements_ios(xml_str):
                t = e["text"].strip()
                if t and t.lower() not in SKIP_TEXTS:
                    key = t.lower()
                    if key not in seen:
                        seen.add(key)
                        all_texts.append(t)

            if page >= scroll_pages:
                break
            _wda_swipe(mid_x, from_y, mid_x, to_y, wda_url, session_id)
    finally:
        keepalive_stop.set()

    print(f"[Sample] Collected {len(all_texts)} unique element texts from screen_0")
    return all_texts


# ---------------------------------------------------------------------------
# Stage 2: generate profile via LLM
# ---------------------------------------------------------------------------

def _heuristic_profile(element_texts: list[str]) -> dict:
    """Fallback: generate a basic profile without LLM.

    Heuristics:
      - Short texts (2-6 chars) with Chinese or mixed case → preserve_navigation
      - Long texts >=8 chars → dynamic_pattern "^.{8,}$"
    """
    preserve = []
    for t in element_texts:
        stripped = t.strip()
        if 2 <= len(stripped) <= 6:
            preserve.append(stripped)
    patterns = ["^.{8,}$"] if any(len(t.strip()) >= 8 for t in element_texts) else []
    print(f"[Profile] Heuristic: {len(patterns)} patterns, {len(preserve)} preserved")
    return {
        "dynamic_patterns": patterns,
        "preserve_navigation": preserve,
    }


def generate_profile(
    app_name: str,
    bundle_id: str,
    element_texts: list[str],
    api_key: str = "EMPTY",
    api_base: str = "http://localhost:8002/v1",
    model: str = "Qwen/Qwen2.5-3B-Instruct",
) -> dict:
    """Use LLM to analyze screen_0 elements and produce an app-specific profile.

    Returns profile dict ready for save_profile().
    """
    from phonecli.llm_client import text_completion
    from phonecli.prompts import PROFILE_GENERATION_PROMPT

    element_list = "\n".join(f"- {t}" for t in element_texts)
    system_prompt = PROFILE_GENERATION_PROMPT.format(
        app_name=app_name, element_list=element_list)

    print(f"[Profile] Analyzing {len(element_texts)} elements with LLM...")
    try:
        rsp = text_completion(system_prompt, "Output the JSON profile.",
                              api_key=api_key, api_base=api_base, model=model,
                              max_tokens=4096, temperature=0.0)
    except Exception as e:
        print(f"[Profile] LLM call failed ({e}), using heuristic fallback")
        rsp = ""

    # Parse JSON from response with fallbacks
    data = None
    if rsp:
        try:
            data = json.loads(rsp.strip())
        except (json.JSONDecodeError, ValueError):
            # Try extracting JSON block
            start = rsp.find("{")
            end = rsp.rfind("}") + 1
            if start >= 0 and end > start:
                try:
                    data = json.loads(rsp[start:end])
                except (json.JSONDecodeError, ValueError):
                    pass

    # Fallback: minimal profile from heuristics
    if not isinstance(data, dict):
        print(f"[Profile] LLM JSON parse failed, using heuristic fallback")
        data = _heuristic_profile(element_texts)

    profile = {
        "app": app_name,
        "bundle_id": bundle_id,
        "dynamic_patterns": data.get("dynamic_patterns", []),
        "preserve_navigation": data.get("preserve_navigation", []),
    }

    print(f"[Profile] Generated: {len(profile['dynamic_patterns'])} patterns, "
          f"{len(profile['preserve_navigation'])} preserved")
    return profile


# ---------------------------------------------------------------------------
# Stage 3: full pipeline — sample → profile → build
# ---------------------------------------------------------------------------

def auto_build(
    wda_url: str,
    session_id: str,
    bundle_id: str,
    app_name: str,
    output_path: str = "phonecli/app_maps/app_map.yaml",
    profile_dir: str = "phonecli/profiles",
    max_screens: int = 50,
    max_depth: int = 3,
    scroll_pages: int = 3,
    redact: bool = True,
    classify: bool = True,
    enrich: bool = True,
    checkpoint_path: str = None,
    llm_api_key: str = "EMPTY",
    llm_api_base: str = "http://localhost:8002/v1",
    llm_model: str = "Qwen/Qwen2.5-3B-Instruct",
) -> str:
    """Full pipeline: sample → generate profile → build with profile.

    Profile patterns filter out obviously dynamic content.
    LLM classify (when enabled) further labels remaining elements as STABLE/DYNAMIC.
    The two work together — profile reduces noise, classify adds precision."""
    import sys

    # Stage 1: sample
    print("\n" + "=" * 50)
    print("[Pipeline] Stage 1/5: Sampling screen_0...")
    print("=" * 50)
    elements = sample_screen0(wda_url, session_id, bundle_id, scroll_pages)

    # Stage 2: generate profile
    print("\n" + "=" * 50)
    print("[Pipeline] Stage 2/5: Generating profile...")
    print("=" * 50)
    profile = generate_profile(app_name, bundle_id, elements,
                               api_key=llm_api_key, api_base=llm_api_base,
                               model=llm_model)

    profile_path = os.path.join(profile_dir, f"{app_name}.yaml")
    os.makedirs(profile_dir, exist_ok=True)
    save_profile(profile, profile_path)
    print(f"[Pipeline] Profile saved: {profile_path}")

    # Stage 3: full build
    print("\n" + "=" * 50)
    print("[Pipeline] Stage 3/5: Full crawl with profile...")
    print("=" * 50)
    from phonecli.build_map import build_app_map

    path = build_app_map(
        wda_url=wda_url, session_id=session_id,
        bundle_id=bundle_id, app_name=app_name,
        output_path=output_path,
        max_screens=max_screens, max_depth=max_depth,
        scroll_pages=scroll_pages,
        redact=redact, classify=classify,
        enrich=enrich,
        checkpoint_path=checkpoint_path,
        llm_api_key=llm_api_key, llm_api_base=llm_api_base, llm_model=llm_model,
        profile=profile,
    )

    # Stage 4: validate
    print("\n" + "=" * 50)
    print("[Pipeline] Stage 4/5: Validating map...")
    print("=" * 50)
    from phonecli.validate_map import validate_map, print_validation_report
    errors, warnings = validate_map(path, profile=profile)
    print(print_validation_report(errors, warnings))

    # Stage 5: sanitize personal data
    print("\n" + "=" * 50)
    print("[Pipeline] Stage 5/5: Sanitizing personal data...")
    print("=" * 50)
    from phonecli.sanitize_map import sanitize_map
    try:
        result = sanitize_map(
            path, output_path=path,
            use_llm=True,
            llm_api_key=llm_api_key, llm_api_base=llm_api_base, llm_model=llm_model,
        )
        return result["path"]
    except Exception as e:
        print(f"[Sanitize] Failed ({e}) — returning unsanitized map.")
        return path
