#!/usr/bin/env python3
"""Phone CLI — iOS phone agent command-line interface via WebDriverAgent (WDA).

All operations exposed as deterministic CLI subcommands with JSON output.

Usage:
    python cli.py device screenshot --output /tmp/s.png
    python cli.py device tap 100 200
    python cli.py macro run --app-map settings_map.yaml --op-id op_wifi
    python cli.py llm map-task --app-map settings_map.yaml --task "Turn on wifi"
    python cli.py vlm act --task "Open Settings" --screenshot /tmp/s.png
"""

import json
import os
import sys
import time
from pathlib import Path
from typing import Optional

# Ensure phonecli package is importable when run directly
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import early so _load_dotenv() runs BEFORE Click resolves envvar=... options
import phonecli  # noqa: F401

import click


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ok(**kwargs) -> dict:
    return {"status": "ok", **kwargs}


def _err(msg: str) -> dict:
    return {"status": "error", "message": msg}


def _output(data: dict):
    click.echo(json.dumps(data, ensure_ascii=False))


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

@click.group()
@click.option("--wda-url", default=None, help="WebDriverAgent URL (default: http://localhost:8100)")
@click.option("--session-id", default=None, help="WDA session ID (auto-created if omitted)")
@click.pass_context
def cli(ctx, wda_url, session_id):
    """Phone CLI — coordinate-based iOS phone automation toolkit."""
    ctx.ensure_object(dict)
    ctx.obj["wda_url"] = wda_url
    ctx.obj["session_id"] = session_id


def _resolve_wda(ctx) -> str:
    """Resolve WDA URL from context or env."""
    return (ctx.obj.get("wda_url")
            or os.getenv("PHONECLI_WDA_URL", "http://localhost:8100"))


def _resolve_session(ctx) -> str:
    """Resolve WDA session ID from context or create one."""
    sid = ctx.obj.get("session_id")
    if sid:
        return sid
    from phonecli.device import create_session, is_wda_ready
    wda = _resolve_wda(ctx)
    if not is_wda_ready(wda):
        return None
    ok, sid = create_session(wda)
    if not ok:
        print(f"Warning: could not create WDA session: {sid}", file=sys.stderr)
        return None
    ctx.obj["session_id"] = sid
    return sid


# ===================================================================
# Device group
# ===================================================================

@cli.group()
def device():
    """Device operations (tap, swipe, screenshot, etc.) via WDA."""


@device.command("screenshot")
@click.option("--output", "-o", required=True, help="Output PNG path")
@click.pass_context
def device_screenshot(ctx, output):
    """Take a screenshot."""
    from phonecli.device import take_screenshot
    ok = take_screenshot(output, _resolve_wda(ctx), _resolve_session(ctx))
    if ok:
        _output(_ok(path=os.path.abspath(output)))
    else:
        _output(_err("Screenshot failed"))


@device.command("xml")
@click.option("--output", "-o", required=True, help="Output XML path")
@click.pass_context
def device_xml(ctx, output):
    """Dump iOS page source XML (XCUITest hierarchy)."""
    from phonecli.device import dump_xml
    ok = dump_xml(output, _resolve_wda(ctx), _resolve_session(ctx))
    if ok:
        _output(_ok(path=os.path.abspath(output)))
    else:
        _output(_err("XML dump failed"))


def _ensure_session(ctx):
    """Resolve session, output error JSON and return None if unavailable."""
    sid = _resolve_session(ctx)
    if sid is None:
        _output(_err("No WDA session available. Ensure WDA is running and accessible."))
        return None
    return sid


@device.command("tap")
@click.argument("x", type=int)
@click.argument("y", type=int)
@click.pass_context
def device_tap(ctx, x, y):
    """Tap at logical coordinates (points)."""
    from phonecli.device import tap
    sid = _ensure_session(ctx)
    if not sid:
        return
    if not tap(x, y, _resolve_wda(ctx), sid):
        _output(_err(f"Tap at ({x},{y}) failed"))
        return
    _output(_ok(x=x, y=y))


@device.command("swipe")
@click.argument("x1", type=int)
@click.argument("y1", type=int)
@click.argument("x2", type=int)
@click.argument("y2", type=int)
@click.option("--duration", type=int, default=400, help="Duration in ms")
@click.pass_context
def device_swipe(ctx, x1, y1, x2, y2, duration):
    """Swipe from (x1,y1) to (x2,y2) in logical coordinates."""
    from phonecli.device import swipe
    sid = _ensure_session(ctx)
    if not sid:
        return
    if not swipe(x1, y1, x2, y2, duration, _resolve_wda(ctx), sid):
        _output(_err(f"Swipe from ({x1},{y1}) to ({x2},{y2}) failed"))
        return
    _output(_ok(x1=x1, y1=y1, x2=x2, y2=y2))


@device.command("text")
@click.argument("text_str")
@click.pass_context
def device_text(ctx, text_str):
    """Type text into focused input field."""
    from phonecli.device import input_text
    sid = _ensure_session(ctx)
    if not sid:
        return
    if not input_text(text_str, _resolve_wda(ctx), sid):
        _output(_err(f"Text input failed"))
        return
    _output(_ok(text=text_str))


@device.command("long-press")
@click.argument("x", type=int)
@click.argument("y", type=int)
@click.option("--duration", type=int, default=3000, help="Duration in ms")
@click.pass_context
def device_long_press(ctx, x, y, duration):
    """Long press at logical coordinates."""
    from phonecli.device import long_press
    sid = _ensure_session(ctx)
    if not sid:
        return
    if not long_press(x, y, duration, _resolve_wda(ctx), sid):
        _output(_err(f"Long press at ({x},{y}) failed"))
        return
    _output(_ok(x=x, y=y))


@device.command("back")
@click.pass_context
def device_back(ctx):
    """iOS back gesture (swipe from left edge)."""
    from phonecli.device import back
    sid = _ensure_session(ctx)
    if not sid:
        return
    if not back(_resolve_wda(ctx), sid):
        _output(_err("Back gesture failed"))
        return
    _output(_ok())


@device.command("home")
@click.pass_context
def device_home(ctx):
    """Press home button (go to home screen)."""
    from phonecli.device import home
    sid = _ensure_session(ctx)
    if not sid:
        return
    if not home(_resolve_wda(ctx), sid):
        _output(_err("Home action failed"))
        return
    _output(_ok())


@device.command("launch")
@click.argument("app")
@click.pass_context
def device_launch(ctx, app):
    """Launch an app by name or bundle ID.

    Examples: \'Settings\', \'Safari\', \'com.apple.Preferences\'
    """
    from phonecli.device import launch_app, resolve_bundle_id
    sid = _ensure_session(ctx)
    if not sid:
        return
    bid = resolve_bundle_id(app) or app
    if not launch_app(bid, _resolve_wda(ctx), sid):
        _output(_err(f"Failed to launch {app}"))
        return
    _output(_ok(app=app, bundle_id=bid))


@device.command("info")
@click.pass_context
def device_info(ctx):
    """Get device info (screen size, current app)."""
    from phonecli.device import get_screen_size, get_current_app
    wda = _resolve_wda(ctx)
    sid = _resolve_session(ctx)
    w, h = get_screen_size(wda, sid)
    app = get_current_app(wda, sid)
    _output(_ok(wda_url=wda, width=w, height=h, current_app=app))


# ===================================================================
# Macro group
# ===================================================================

@cli.group()
def macro():
    """App map macro operations (list, run, build)."""


@macro.command("list")
@click.option("--app-map", "-m", required=True, help="Path to app map YAML")
def macro_list(app_map):
    """List available operations in an app map."""
    if not os.path.exists(app_map):
        _output(_err(f"App map not found: {app_map}"))
        return
    from phonecli.app_map import AppMap
    am = AppMap(app_map)
    ops = am.build_operations()
    catalog = am.format_ops_catalog(ops)
    op_list = [
        {"id": o.id, "description": o.description,
         "type": o.type, "steps": len(o.macro)}
        for o in ops.values()
    ]
    _output(_ok(app=am.app_name, package=am.package,
                screen_w=am.screen_w, screen_h=am.screen_h,
                screen_count=len(am.screens), operation_count=len(ops),
                operations=op_list, catalog=catalog))


@macro.command("run")
@click.option("--app-map", "-m", required=True, help="Path to app map YAML")
@click.option("--op-id", "-o", required=True, help="Operation ID to run")
@click.pass_context
def macro_run(ctx, app_map, op_id):
    """Replay a macro operation's action sequence."""
    if not os.path.exists(app_map):
        _output(_err(f"App map not found: {app_map}"))
        return

    wda = _resolve_wda(ctx)
    sid = _resolve_session(ctx)
    if not sid:
        _output(_err("No WDA session available"))
        return
    from phonecli.app_map import AppMap
    from phonecli.device import tap, swipe, launch_app, force_stop

    am = AppMap(app_map)
    ops = am.build_operations()
    if op_id not in ops:
        similar = [o.id for o in ops.values() if op_id.lower() in o.id.lower()]
        _output(_err(f"Operation '{op_id}' not found. Similar: {similar[:5]}"))
        return

    op = ops[op_id]
    results = []
    for i, step in enumerate(op.macro):
        action = step.get("action", "")
        ok = True
        if action == "launch":
            ok = launch_app(step.get("bundle_id", ""), wda, sid)
        elif action == "tap":
            ok = tap(step.get("x"), step.get("y"), wda, sid)
        elif action == "swipe":
            ok = swipe(step.get("x1"), step.get("y1"), step.get("x2"), step.get("y2"),
                       step.get("duration", 400), wda, sid)
        elif action == "force_stop":
            ok = force_stop(step.get("bundle_id", ""), wda, sid)
        else:
            ok = False
        results.append({"step": i + 1, "action": action, "ok": ok})
        if not ok:
            _output(_err(f"Step {i+1} failed: {action}"))
            return
        if "wait" in step:
            time.sleep(step["wait"])
    _output(_ok(operation=op.id, description=op.description,
                type=op.type, steps=len(op.macro), results=results))


@macro.command("build")
@click.option("--bundle-id", "-b", required=True, help="iOS bundle ID (e.g. com.apple.Preferences)")
@click.option("--app-name", "-a", required=True, help="Human-readable app name")
@click.option("--output", "-o", default="phonecli/app_maps/app_map.yaml", help="Output YAML path")
@click.option("--max-screens", type=int, default=50, help="Maximum screens to crawl")
@click.option("--max-depth", type=int, default=3, help="Maximum navigation depth")
@click.option("--scroll-pages", type=int, default=3, help="Max scroll pages per screen")
@click.option("--redact/--no-redact", default=True, help="Redact PII (email, phone, name, etc.)")
@click.option("--classify/--no-classify", default=True, help="Use LLM to classify stable vs dynamic elements (default: on)")
@click.option("--enrich/--no-enrich", default=True, help="Use LLM to add aliases, descriptions, and app metadata (default: on)")
@click.option("--profile", "-p", default=None, help="Path to app profile YAML (filters dynamic content, works alongside classify)")
@click.option("--checkpoint", "-c", default=None, help="Save progress to checkpoint file (resumable if interrupted)")
@click.option("--resume", "-r", "resume_from", default=None, help="Resume from a checkpoint file")
@click.option("--llm-api-key", envvar="PHONECLI_LLM_API_KEY", default="EMPTY")
@click.option("--llm-api-base", envvar="PHONECLI_LLM_API_BASE", default="http://localhost:8002/v1")
@click.option("--llm-model", envvar="PHONECLI_LLM_MODEL", default="Qwen/Qwen2.5-3B-Instruct")
@click.pass_context
def macro_build(ctx, bundle_id, app_name, output, max_screens, max_depth,
                scroll_pages, redact, classify, enrich, profile, checkpoint,
                resume_from, llm_api_key, llm_api_base, llm_model):
    """Build an app map by crawling an iOS app via WDA.

    Use --profile to pass an app-specific profile (generated by macro sample + macro profile).
    Profile patterns filter dynamic content; classify further labels remaining elements.
    """
    llm_api_key = _env_or(llm_api_key, "API_KEY", "EMPTY")
    llm_api_base = _env_or(llm_api_base, "API_BASE", "http://localhost:8002/v1")
    llm_model = _env_or(llm_model, "MODEL_NAME", "Qwen/Qwen2.5-3B-Instruct")
    wda = _resolve_wda(ctx)
    sid = _resolve_session(ctx)
    if not sid:
        _output(_err("No WDA session. Ensure WDA is running and accessible."))
        return

    # Load profile if provided
    profile_data = None
    if profile:
        from phonecli.profile_builder import load_profile
        profile_data = load_profile(profile)
        if not profile_data:
            _output(_err(f"Profile not found or invalid: {profile}"))
            return

    from phonecli.build_map import build_app_map
    try:
        path = build_app_map(
            wda_url=wda, session_id=sid,
            bundle_id=bundle_id, app_name=app_name,
            output_path=output,
            max_screens=max_screens, max_depth=max_depth,
            scroll_pages=scroll_pages,
            redact=redact,
            classify=classify,
            enrich=enrich,
            llm_api_key=llm_api_key, llm_api_base=llm_api_base, llm_model=llm_model,
            profile=profile_data,
            checkpoint_path=checkpoint,
            resume_from=resume_from,
        )
        _output(_ok(path=os.path.abspath(path)))
    except Exception as e:
        _output(_err(f"Build failed: {e}"))


@macro.command("sample")
@click.option("--bundle-id", "-b", required=True, help="iOS bundle ID")
@click.option("--app-name", "-a", required=True, help="Human-readable app name")
@click.option("--output", "-o", default=None, help="Save element list to file (default: print to stdout)")
@click.pass_context
def macro_sample(ctx, bundle_id, app_name, output):
    """Sample screen_0 to collect all visible element texts (Stage 1/3)."""
    wda = _resolve_wda(ctx)
    sid = _resolve_session(ctx)
    if not sid:
        _output(_err("No WDA session. Ensure WDA is running and accessible."))
        return

    from phonecli.profile_builder import sample_screen0
    try:
        texts = sample_screen0(wda, sid, bundle_id)
    except Exception as e:
        _output(_err(f"Sample failed: {e}"))
        return

    if output:
        with open(output, "w") as f:
            for t in texts:
                f.write(t + "\n")
        _output(_ok(app=app_name, count=len(texts), path=os.path.abspath(output)))
    else:
        _output(_ok(app=app_name, count=len(texts), elements=texts))


@macro.command("profile")
@click.option("--app-name", "-a", required=True, help="Human-readable app name")
@click.option("--bundle-id", "-b", required=True, help="iOS bundle ID")
@click.option("--sample-file", "-s", required=True, help="File with element texts (one per line, from macro sample)")
@click.option("--output", "-o", default=None, help="Output profile YAML path (default: profiles/<app>.yaml)")
@click.option("--llm-api-key", envvar="PHONECLI_LLM_API_KEY", default="EMPTY")
@click.option("--llm-api-base", envvar="PHONECLI_LLM_API_BASE", default="http://localhost:8002/v1")
@click.option("--llm-model", envvar="PHONECLI_LLM_MODEL", default="Qwen/Qwen2.5-3B-Instruct")
def macro_profile(app_name, bundle_id, sample_file, output, llm_api_key, llm_api_base, llm_model):
    """Generate app profile from sampled element texts (Stage 2/3).

    Reads element texts from --sample-file, sends to LLM for analysis,
    and outputs an app-specific profile YAML with dynamic_patterns and preserve_navigation.
    """
    llm_api_key = _env_or(llm_api_key, "API_KEY", "EMPTY")
    llm_api_base = _env_or(llm_api_base, "API_BASE", "http://localhost:8002/v1")
    llm_model = _env_or(llm_model, "MODEL_NAME", "Qwen/Qwen2.5-3B-Instruct")

    if not os.path.exists(sample_file):
        _output(_err(f"Sample file not found: {sample_file}"))
        return

    with open(sample_file, "r") as f:
        texts = [line.strip() for line in f if line.strip()]

    from phonecli.profile_builder import generate_profile, save_profile
    try:
        profile = generate_profile(app_name, bundle_id, texts,
                                   api_key=llm_api_key, api_base=llm_api_base,
                                   model=llm_model)
    except Exception as e:
        _output(_err(f"Profile generation failed: {e}"))
        return

    output_path = output or f"phonecli/profiles/{app_name}.yaml"
    save_profile(profile, output_path)
    _output(_ok(app=app_name, bundle_id=bundle_id,
                dynamic_patterns=len(profile["dynamic_patterns"]),
                preserved=len(profile["preserve_navigation"]),
                path=os.path.abspath(output_path)))


@macro.command("auto-build")
@click.option("--bundle-id", "-b", required=True, help="iOS bundle ID")
@click.option("--app-name", "-a", required=True, help="Human-readable app name")
@click.option("--output", "-o", default="phonecli/app_maps/app_map.yaml", help="Output YAML path")
@click.option("--profile-dir", default="phonecli/profiles", help="Directory for generated profiles")
@click.option("--max-screens", type=int, default=50, help="Maximum screens to crawl")
@click.option("--max-depth", type=int, default=3, help="Maximum navigation depth")
@click.option("--scroll-pages", type=int, default=3, help="Max scroll pages per screen")
@click.option("--redact/--no-redact", default=True, help="Redact PII (email, phone, name, etc.)")
@click.option("--classify/--no-classify", default=True, help="Use LLM to classify stable vs dynamic elements (default: on)")
@click.option("--enrich/--no-enrich", default=True, help="Use LLM to add aliases, descriptions (default: on)")
@click.option("--checkpoint", "-c", default=None, help="Save/resume checkpoint file for build stage")
@click.option("--resume", "-r", "resume_from", default=None, help="Resume build from checkpoint (skips sample+profile stages)")
@click.option("--llm-api-key", envvar="PHONECLI_LLM_API_KEY", default="EMPTY")
@click.option("--llm-api-base", envvar="PHONECLI_LLM_API_BASE", default="http://localhost:8002/v1")
@click.option("--llm-model", envvar="PHONECLI_LLM_MODEL", default="Qwen/Qwen2.5-3B-Instruct")
@click.pass_context
def macro_auto_build(ctx, bundle_id, app_name, output, profile_dir, max_screens,
                      max_depth, scroll_pages, redact, classify, enrich, checkpoint, resume_from,
                      llm_api_key, llm_api_base, llm_model):
    """Full pipeline: sample → profile → build (Stage 1/2/3).

    One command that samples screen_0, generates an app-specific filtering profile
    via LLM, and then runs the full crawl using that profile.
    """
    llm_api_key = _env_or(llm_api_key, "API_KEY", "EMPTY")
    llm_api_base = _env_or(llm_api_base, "API_BASE", "http://localhost:8002/v1")
    llm_model = _env_or(llm_model, "MODEL_NAME", "Qwen/Qwen2.5-3B-Instruct")
    wda = _resolve_wda(ctx)
    sid = _resolve_session(ctx)
    if not sid:
        _output(_err("No WDA session. Ensure WDA is running and accessible."))
        return

    from phonecli.profile_builder import auto_build, load_profile

    if resume_from:
        # Resume mode: load existing profile, skip sample+profile stages
        ck = None
        try:
            import json
            with open(resume_from, "r") as f:
                ck = json.load(f)
        except Exception:
            pass
        if not ck:
            _output(_err(f"Checkpoint not found or invalid: {resume_from}"))
            return
        profile_path = os.path.join(profile_dir, f"{app_name}.yaml")
        profile_data = load_profile(profile_path)
        if not profile_data:
            _output(_err(f"Profile required for resume, not found: {profile_path}"))
            return
        from phonecli.build_map import build_app_map
        try:
            path = build_app_map(
                wda_url=wda, session_id=sid,
                bundle_id=bundle_id, app_name=app_name,
                output_path=output,
                max_screens=max_screens, max_depth=max_depth,
                scroll_pages=scroll_pages,
                redact=redact, classify=classify, enrich=enrich,
                llm_api_key=llm_api_key, llm_api_base=llm_api_base, llm_model=llm_model,
                profile=profile_data,
                checkpoint_path=checkpoint or resume_from,
                resume_from=resume_from,
            )
        except Exception as e:
            _output(_err(f"Resume build failed: {e}"))
            return

        # Stage 4: validate
        from phonecli.validate_map import validate_map, print_validation_report
        errors, warnings = validate_map(path, profile=profile_data)
        print(print_validation_report(errors, warnings))

        # Stage 5: sanitize
        from phonecli.sanitize_map import sanitize_map
        try:
            result = sanitize_map(
                path, output_path=path,
                use_llm=True,
                llm_api_key=llm_api_key, llm_api_base=llm_api_base, llm_model=llm_model,
            )
            _output(_ok(path=os.path.abspath(result["path"])))
        except Exception as e:
            print(f"[Sanitize] Failed ({e}) — returning unsanitized map.")
            _output(_ok(path=os.path.abspath(path)))
        return

    try:
        path = auto_build(
            wda_url=wda, session_id=sid,
            bundle_id=bundle_id, app_name=app_name,
            output_path=output,
            profile_dir=profile_dir,
            max_screens=max_screens, max_depth=max_depth,
            scroll_pages=scroll_pages,
            redact=redact, classify=classify, enrich=enrich,
            checkpoint_path=checkpoint,
            llm_api_key=llm_api_key, llm_api_base=llm_api_base, llm_model=llm_model,
        )
        _output(_ok(path=os.path.abspath(path)))
    except Exception as e:
        _output(_err(f"Auto-build failed: {e}"))


@macro.command("validate")
@click.option("--map-file", "-m", required=True, help="Path to app map YAML")
@click.option("--profile", "-p", default=None, help="Path to app profile YAML (optional)")
def macro_validate(map_file, profile):
    """Validate an app map for errors, data quality, and profile effectiveness."""
    if not os.path.exists(map_file):
        _output(_err(f"Map file not found: {map_file}"))
        return

    profile_data = None
    if profile:
        from phonecli.profile_builder import load_profile
        profile_data = load_profile(profile)
        if not profile_data:
            _output(_err(f"Profile not found or invalid: {profile}"))
            return

    from phonecli.validate_map import validate_map
    errors, warnings = validate_map(map_file, profile=profile_data)
    _output(_ok(
        map_file=os.path.abspath(map_file),
        errors=len(errors), warnings=len(warnings),
        error_list=errors, warning_list=warnings,
    ))


@macro.command("sanitize")
@click.option("--map-file", "-m", required=True, help="Path to app map YAML")
@click.option("--output", "-o", default=None, help="Output path (default: overwrite map)")
@click.option("--no-llm", is_flag=True, default=False, help="Skip LLM, use rule-based classification")
@click.option("--llm-api-key", envvar="PHONECLI_LLM_API_KEY", default="EMPTY")
@click.option("--llm-api-base", envvar="PHONECLI_LLM_API_BASE", default="http://localhost:8002/v1")
@click.option("--llm-model", envvar="PHONECLI_LLM_MODEL", default="Qwen/Qwen2.5-3B-Instruct")
def macro_sanitize(map_file, output, no_llm, llm_api_key, llm_api_base, llm_model):
    """Sanitize an app map: detect and replace personal data.

    Uses LLM (with screen context) to classify personal data, then globally
    replaces with placeholders [Name], [Device], [App], etc.
    Use --no-llm for rule-based fallback.
    """
    if not os.path.exists(map_file):
        _output(_err(f"Map file not found: {map_file}"))
        return

    llm_api_key = _env_or(llm_api_key, "API_KEY", "EMPTY")
    llm_api_base = _env_or(llm_api_base, "API_BASE", "http://localhost:8002/v1")
    llm_model = _env_or(llm_model, "MODEL_NAME", "Qwen/Qwen2.5-3B-Instruct")

    from phonecli.sanitize_map import sanitize_map
    try:
        result = sanitize_map(
            map_file, output_path=output,
            use_llm=not no_llm,
            llm_api_key=llm_api_key, llm_api_base=llm_api_base, llm_model=llm_model,
        )
        _output(_ok(
            map_file=os.path.abspath(map_file),
            output=os.path.abspath(result["path"]),
            replaced=result["replaced"],
            replacements=result["replacements"],
        ))
    except Exception as e:
        _output(_err(f"Sanitize failed: {e}"))


# ===================================================================
# LLM group (text-only)
# ===================================================================

@cli.group()
def llm():
    """Text-only LLM operations (task mapping, XML verification)."""


def _env_or(key: str, fallback_env: str, default: str) -> str:
    """Resolve value: explicit arg → env var → fallback env var → default."""
    if key and key != default:
        return key
    return os.getenv(fallback_env, default)


@llm.command("map-task")
@click.option("--app-map", "-m", required=True, help="Path to app map YAML")
@click.option("--task", "-t", required=True, help="Task description")
@click.option("--memory-hints", default="", help="Memory context from previous tasks")
@click.option("--api-key", envvar="PHONECLI_LLM_API_KEY", default="EMPTY")
@click.option("--api-base", envvar="PHONECLI_LLM_API_BASE", default="http://localhost:8002/v1")
@click.option("--model", envvar="PHONECLI_LLM_MODEL", default="Qwen/Qwen2.5-3B-Instruct")
def llm_map_task(app_map, task, memory_hints, api_key, api_base, model):
    """Map a natural language task to an app map operation."""
    api_key = _env_or(api_key, "API_KEY", "EMPTY")
    api_base = _env_or(api_base, "API_BASE", "http://localhost:8002/v1")
    model = _env_or(model, "MODEL_NAME", "Qwen/Qwen2.5-3B-Instruct")
    if not os.path.exists(app_map):
        _output(_err(f"App map not found: {app_map}"))
        return
    from phonecli.app_map import AppMap
    from phonecli.llm_client import text_completion
    from phonecli.prompts import MACRO_PLAN_PROMPT
    import re

    am = AppMap(app_map)
    ops = am.build_operations()
    catalog = am.format_ops_catalog(ops)
    memory_ctx = f"## Context from previous tasks\n{memory_hints}\n\n" if memory_hints else ""
    system_prompt = MACRO_PLAN_PROMPT.format(
        app_name=am.app_name, operations_catalog=catalog,
        memory_context=memory_ctx)
    try:
        rsp = text_completion(system_prompt, f"Task: {task}",
                              api_key=api_key, api_base=api_base, model=model)
    except Exception as e:
        _output(_err(f"LLM call failed: {e}"))
        return

    op_match = re.search(r'(?:MACRO_VLM|OP):\s*(.*)', rsp, re.IGNORECASE)
    need_match = re.search(r'NEED_VLM:\s*(.*)', rsp, re.IGNORECASE)
    finish_match = re.search(r'FINISH:\s*(.*)', rsp, re.IGNORECASE)

    if op_match:
        raw = op_match.group(1).strip()
        is_combo = op_match.group(0).upper().startswith("MACRO_VLM")
        if raw in ops:
            op = ops[raw]
            _output(_ok(result="op_found", op_id=raw,
                        description=op.description, type=op.type,
                        is_macro_vlm=is_combo))
        else:
            similar = [o.id for o in ops.values() if raw.lower() in o.id.lower()]
            _output(_ok(result="op_not_found", requested=raw,
                        similar=similar[:5], is_macro_vlm=is_combo))
    elif need_match:
        _output(_ok(result="need_vlm", reason=need_match.group(1).strip()))
    elif finish_match:
        _output(_ok(result="finish", answer=finish_match.group(1).strip()))
    else:
        _output(_ok(result="unrecognized", raw_response=rsp[:200]))


@llm.command("xml-verify")
@click.option("--task", "-t", required=True)
@click.option("--xml-file", required=True)
@click.option("--api-key", envvar="PHONECLI_LLM_API_KEY", default="EMPTY")
@click.option("--api-base", envvar="PHONECLI_LLM_API_BASE", default="http://localhost:8002/v1")
@click.option("--model", envvar="PHONECLI_LLM_MODEL", default="Qwen/Qwen2.5-3B-Instruct")
def llm_xml_verify(task, xml_file, api_key, api_base, model):
    """Verify task completion using page source text only."""
    api_key = _env_or(api_key, "API_KEY", "EMPTY")
    api_base = _env_or(api_base, "API_BASE", "http://localhost:8002/v1")
    model = _env_or(model, "MODEL_NAME", "Qwen/Qwen2.5-3B-Instruct")
    if not os.path.exists(xml_file):
        _output(_err(f"XML file not found: {xml_file}"))
        return
    from phonecli.llm_client import text_completion
    from phonecli.prompts import XML_VERIFY_PROMPT
    import re
    with open(xml_file, "r", encoding="utf-8") as f:
        xml_content = f.read()
    try:
        rsp = text_completion(XML_VERIFY_PROMPT,
                              f"Task: {task}\n\nAccessibility text:\n{xml_content[:8000]}",
                              api_key=api_key, api_base=api_base, model=model)
    except Exception as e:
        _output(_err(f"LLM call failed: {e}"))
        return
    finish_match = re.search(r'FINISH:\s*(.*)', rsp, re.IGNORECASE)
    need_match = re.search(r'NEED_VLM:\s*(.*)', rsp, re.IGNORECASE)
    if finish_match:
        answer = finish_match.group(1).strip()
        action_words = ["click", "tap", "press", "button", "navigate",
                       "open the", "select the", "scroll", "swipe", "type"]
        if any(w in answer.lower() for w in action_words):
            _output(_ok(result="need_vlm", reason=f"XML gave instruction: {answer}"))
        else:
            _output(_ok(result="finish", answer=answer))
    elif need_match:
        _output(_ok(result="need_vlm", reason=need_match.group(1).strip()))
    else:
        _output(_ok(result="need_vlm", reason=f"Unrecognized response: {rsp[:100]}"))


@llm.command("plan")
@click.option("--task", "-t", required=True, help="Complex task description")
@click.option("--app-map", "-m", "app_maps", multiple=True, required=True,
              help="Path to app map YAML (repeatable)")
@click.option("--memory-hints", default="", help="Memory context from previous tasks")
@click.option("--api-key", envvar="PHONECLI_LLM_API_KEY", default="EMPTY")
@click.option("--api-base", envvar="PHONECLI_LLM_API_BASE", default="http://localhost:8002/v1")
@click.option("--model", envvar="PHONECLI_LLM_MODEL", default="Qwen/Qwen2.5-3B-Instruct")
def llm_plan(task, app_maps, memory_hints, api_key, api_base, model):
    """Decompose a complex multi-app task into single-app subtasks."""
    api_key = _env_or(api_key, "API_KEY", "EMPTY")
    api_base = _env_or(api_base, "API_BASE", "http://localhost:8002/v1")
    model = _env_or(model, "MODEL_NAME", "Qwen/Qwen2.5-3B-Instruct")

    from phonecli.app_map import AppMap
    from phonecli.llm_client import text_completion
    from phonecli.prompts import TASK_DECOMPOSE_PROMPT

    apps_entries = []
    for path in app_maps:
        if not os.path.exists(path):
            continue
        am = AppMap(path)
        apps_entries.append(f"- {am.app_name} ({am.package})")

    if not apps_entries:
        _output(_err("No valid app maps provided"))
        return

    memory_context = ""
    if memory_hints:
        memory_context = f"\n## Past Experience\n{memory_hints}\n"

    system_prompt = TASK_DECOMPOSE_PROMPT.format(
        apps_catalog="\n".join(apps_entries),
        task=task,
        memory_context=memory_context,
    )

    rsp = text_completion(system_prompt, "Output the JSON plan.",
                          api_key=api_key, api_base=api_base, model=model,
                          max_tokens=2048, temperature=0.0)

    plan = None
    try:
        plan = json.loads(rsp.strip())
    except (json.JSONDecodeError, ValueError):
        start = rsp.find("[")
        end = rsp.rfind("]") + 1
        if start >= 0 and end > start:
            try:
                plan = json.loads(rsp[start:end])
            except (json.JSONDecodeError, ValueError):
                pass

    if not isinstance(plan, list) or len(plan) == 0:
        _output(_ok(plan=[], steps=0, result="parse_failed",
                    raw_response=rsp[:500]))
        return

    _output(_ok(plan=plan, steps=len(plan), result="ok"))


# ===================================================================
# VLM group (vision)
# ===================================================================

@cli.group()
def vlm():
    """Vision-language model operations (screenshot-based actions)."""


@vlm.command("act")
@click.option("--task", "-t", required=True)
@click.option("--screenshot", "-s", required=True, help="Path to screenshot PNG")
@click.option("--history", "-H", default="", help="Previous observation history")
@click.option("--system-prompt", default=None)
@click.option("--api-key", envvar="PHONECLI_VLM_API_KEY", default="EMPTY")
@click.option("--api-base", envvar="PHONECLI_VLM_API_BASE", default="http://localhost:8002/v1")
@click.option("--model", envvar="PHONECLI_VLM_MODEL", default="Qwen/Qwen2.5-3B-Instruct")
def vlm_act(task, screenshot, history, system_prompt, api_key, api_base, model):
    """Single VLM step: screenshot + task → action."""
    api_key = _env_or(api_key, "API_KEY", "EMPTY")
    api_base = _env_or(api_base, "API_BASE", "http://localhost:8002/v1")
    model = _env_or(model, "MODEL_NAME", "Qwen/Qwen2.5-3B-Instruct")
    if not os.path.exists(screenshot):
        _output(_err(f"Screenshot not found: {screenshot}"))
        return
    from phonecli.llm_client import vision_completion
    from phonecli.prompts import COORDINATE_VLM_PROMPT
    from phonecli.agent import parse_action

    sp = system_prompt or COORDINATE_VLM_PROMPT
    sp = sp + f"\n\nTask Instruction: {task}"
    user_text = history + "\nCurrent screenshot:" if history else "Current screenshot:"
    try:
        rsp = vision_completion(sp, user_text, [screenshot],
                                api_key=api_key, api_base=api_base, model=model)
    except Exception as e:
        _output(_err(f"VLM call failed: {e}"))
        return
    action = parse_action(rsp)
    if action is None:
        _output(_err(f"Could not parse action from: {rsp[:200]}"))
        return
    _output(_ok(action=action, raw_response=rsp))


@vlm.command("verify")
@click.option("--task", "-t", required=True)
@click.option("--screenshot", "-s", required=True)
@click.option("--api-key", envvar="PHONECLI_VLM_API_KEY", default="EMPTY")
@click.option("--api-base", envvar="PHONECLI_VLM_API_BASE", default="http://localhost:8002/v1")
@click.option("--model", envvar="PHONECLI_VLM_MODEL", default="Qwen/Qwen2.5-3B-Instruct")
def vlm_verify(task, screenshot, api_key, api_base, model):
    """Quick VLM verification: is the task complete?"""
    api_key = _env_or(api_key, "API_KEY", "EMPTY")
    api_base = _env_or(api_base, "API_BASE", "http://localhost:8002/v1")
    model = _env_or(model, "MODEL_NAME", "Qwen/Qwen2.5-3B-Instruct")
    if not os.path.exists(screenshot):
        _output(_err(f"Screenshot not found: {screenshot}"))
        return
    from phonecli.llm_client import vision_completion
    from phonecli.prompts import VLM_VERIFY_PROMPT
    import re
    sp = VLM_VERIFY_PROMPT.format(task=task)
    try:
        rsp = vision_completion(sp, "Check the screenshot.", [screenshot],
                                api_key=api_key, api_base=api_base, model=model,
                                max_tokens=256)
    except Exception as e:
        _output(_err(f"VLM call failed: {e}"))
        return
    complete_match = re.search(r'COMPLETE:\s*(.*)', rsp, re.IGNORECASE)
    incomplete_match = re.search(r'INCOMPLETE:\s*(.*)', rsp, re.IGNORECASE)

    # If both appear, prefer the one that comes first
    if complete_match and incomplete_match:
        if complete_match.start() < incomplete_match.start():
            msg = complete_match.group(1).strip()
            # Reject COMPLETE that describes an incomplete state
            negations = ["尚未", "还没", "没有完成", "not yet", "still need",
                         "未完成", "需要", "incomplete", "未找到", "找不到"]
            if any(n in msg for n in negations):
                _output(_ok(result="incomplete", reason=msg))
            else:
                _output(_ok(result="complete", message=msg))
        else:
            _output(_ok(result="incomplete",
                        reason=incomplete_match.group(1).strip()))
    elif complete_match:
        msg = complete_match.group(1).strip()
        negations = ["尚未", "还没", "没有完成", "not yet", "still need",
                     "未完成", "需要", "incomplete", "未找到", "找不到"]
        if any(n in msg for n in negations):
            _output(_ok(result="incomplete", reason=msg))
        else:
            _output(_ok(result="complete", message=msg))
    elif incomplete_match:
        _output(_ok(result="incomplete",
                    reason=incomplete_match.group(1).strip()))
    else:
        _output(_ok(result="unrecognized", raw_response=rsp[:200]))


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    cli()
