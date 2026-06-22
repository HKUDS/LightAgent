"""Autonomous mode commands for the OpenPhone CLI.

These commands use OpenPhone's built-in VLM to plan and execute tasks
autonomously via the Ralph Loop (EXECUTE → EVALUATE → FIX → REPEAT).

Usage:
    openphone run <task> [--openrouter] [--model-name ...]
    openphone daemon [--openrouter] [--model-name ...]
    openphone learn [app] [--describe ...]
"""

import argparse
import os
import sys
from pathlib import Path

# Ensure project root is on sys.path so PhoneClaw imports work
_project_root = Path(__file__).parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from PhoneClaw.agent import OPENROUTER_BASE_URL

# Lazily imported modules (deferred to avoid heavy transitive deps on --help/--version)
_phoneclaw_modules: dict = {}


def _get_phoneclaw(module_name: str):
    """Lazy import a PhoneClaw module."""
    if module_name not in _phoneclaw_modules:
        import importlib
        _phoneclaw_modules[module_name] = importlib.import_module(f"PhoneClaw.{module_name}")
    return _phoneclaw_modules[module_name]


def _get_phoneclaw_attr(module_name: str, *attrs: str):
    """Lazy import and get attributes from a PhoneClaw module."""
    mod = _get_phoneclaw(module_name)
    if len(attrs) == 1:
        return getattr(mod, attrs[0])
    return tuple(getattr(mod, a) for a in attrs)


def _get_run_phoneclaw_attr(*attrs: str):
    """Lazy import from PhoneClaw.run_phoneclaw."""
    return _get_phoneclaw_attr("run_phoneclaw", *attrs)


# ---------------------------------------------------------------------------
# Shared setup helpers
# ---------------------------------------------------------------------------

def _setup_device(args: argparse.Namespace):
    """Connect to WDA and return shared device components."""
    IOSConnection = _get_phoneclaw_attr("connection", "IOSConnection")
    IOSController = _get_phoneclaw_attr("controller", "IOSController")
    IOSExecutor = _get_phoneclaw_attr("executor", "IOSExecutor")

    conn = IOSConnection(wda_url=args.wda_url)
    if not conn.is_wda_ready():
        raise ConnectionError(f"WebDriverAgent not ready at {args.wda_url}")

    ok, session_id = conn.start_wda_session()
    if not ok:
        raise ConnectionError(f"Failed to start WDA session: {session_id}")

    controller = IOSController(wda_url=args.wda_url, session_id=session_id)
    executor = IOSExecutor(wda_url=args.wda_url, session_id=session_id)
    return controller, executor, session_id


def _setup_agents(args: argparse.Namespace):
    """Create executor and evaluator VLM agent instances."""
    _build_agent = _get_run_phoneclaw_attr("_build_agent")
    TaskPlanner = _get_phoneclaw_attr("planner", "TaskPlanner")
    SubTaskEvaluator = _get_phoneclaw_attr("evaluator", "SubTaskEvaluator")

    common = dict(
        use_openrouter=args.openrouter,
        openrouter_site_url=args.openrouter_site_url,
        openrouter_app_title=args.openrouter_app_title,
    )

    exec_agent = _build_agent(
        api_key=args.openrouter_api_key if args.openrouter else args.api_key,
        model_name=args.model_name,
        api_base=args.openrouter_base_url if args.openrouter else args.api_base,
        agent_type=args.agent_type,
        **common,
    )

    eval_model_name = args.eval_model_name or args.model_name
    eval_api_base = args.eval_api_base or (args.openrouter_base_url if args.openrouter else args.api_base)
    eval_api_key = args.eval_api_key or (args.openrouter_api_key if args.openrouter else args.api_key)

    eval_agent = _build_agent(
        api_key=eval_api_key,
        model_name=eval_model_name,
        api_base=eval_api_base,
        agent_type=args.agent_type,
        **common,
    )

    planner = TaskPlanner(agent=exec_agent)
    evaluator = SubTaskEvaluator(agent=eval_agent)
    return exec_agent, eval_agent, planner, evaluator


def _build_run_namespace(kwargs: dict) -> argparse.Namespace:
    """Build a minimal argparse.Namespace with all attributes needed by PhoneClaw internals."""
    defaults = {
        "wda_url": os.getenv("WDA_URL", "http://localhost:8100"),
        "openrouter": bool(os.getenv("OPENROUTER_API_KEY")),
        "openrouter_api_key": os.getenv("OPENROUTER_API_KEY", ""),
        "openrouter_base_url": OPENROUTER_BASE_URL,
        "openrouter_site_url": os.getenv("OPENROUTER_SITE_URL", "None"),
        "openrouter_app_title": os.getenv("OPENROUTER_APP_TITLE", "PhoneClaw"),
        "model_name": os.getenv("OPENROUTER_MODEL", os.getenv("MODEL_NAME", "z-ai/glm-4.6v")),
        "api_base": os.getenv("API_BASE", "http://localhost:8002/v1"),
        "api_key": os.getenv("API_KEY", "EMPTY"),
        "agent_type": os.getenv("AGENT_TYPE", "OpenAIAgent"),
        "eval_model_name": os.getenv("EVAL_OPENROUTER_MODEL", os.getenv("EVAL_MODEL_NAME", None)),
        "eval_api_base": os.getenv("EVAL_API_BASE", None),
        "eval_api_key": os.getenv("EVAL_API_KEY", None),
        "max_rounds": 100,
        "max_fix_retries": 3,
        "request_interval": 2.0,
        "no_skip_failed": False,
        "keepalive_interval": 0,
        "task_dir": None,
        "resume": False,
        "memory_path": None,
        "no_memory": False,
        "experience_path": None,
        "no_experience": False,
        "interactive": False,
        "learn": False,
        "task": "",
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


# ---------------------------------------------------------------------------
# run
# ---------------------------------------------------------------------------

def cmd_run(args: argparse.Namespace) -> dict:
    """Execute a single task via Ralph Loop."""
    _run_single_task = _get_run_phoneclaw_attr("_run_single_task")
    UserMemory = _get_phoneclaw_attr("memory", "UserMemory")
    ExperienceLog = _get_phoneclaw_attr("experience", "ExperienceLog")

    run_args = _build_run_namespace(vars(args))

    try:
        controller, executor, session_id = _setup_device(run_args)
        exec_agent, eval_agent, planner, evaluator = _setup_agents(run_args)

        task = run_args.task
        if not task:
            return {"success": False, "error": {"code": "NO_TASK", "message": "No task specified"}}

        print(f"[OpenPhone] Task: {task}")
        print(f"[OpenPhone] Model: {run_args.model_name}")

        _run_single_task(
            task_instruction=task,
            args=run_args,
            controller=controller,
            executor=executor,
            exec_agent=exec_agent,
            eval_agent=eval_agent,
            planner=planner,
            evaluator=evaluator,
            task_dir_override=run_args.task_dir,
            resume=run_args.resume,
            memory=UserMemory(profile_path=run_args.memory_path) if not run_args.no_memory else None,
            experience=ExperienceLog(log_path=run_args.experience_path) if not run_args.no_experience else None,
        )

        return {"success": True, "task": task}

    except ConnectionError as e:
        return {"success": False, "error": {"code": "CONNECTION_ERROR", "message": str(e)}}
    except Exception as e:
        return {"success": False, "error": {"code": "EXECUTION_ERROR", "message": str(e)}}


# ---------------------------------------------------------------------------
# daemon
# ---------------------------------------------------------------------------

def cmd_daemon(args: argparse.Namespace) -> dict:
    """Start interactive daemon mode (REPL for continuous task input)."""
    _run_interactive_loop = _get_run_phoneclaw_attr("_run_interactive_loop")
    ScreenKeepalive = _get_phoneclaw_attr("keepalive", "ScreenKeepalive")

    run_args = _build_run_namespace(vars(args))

    try:
        controller, executor, session_id = _setup_device(run_args)
        exec_agent, eval_agent, planner, evaluator = _setup_agents(run_args)

        interval = run_args.keepalive_interval if run_args.keepalive_interval > 0 else 30.0
        keepalive = ScreenKeepalive(
            wda_url=run_args.wda_url,
            session_id=session_id,
            interval=interval,
            verbose=False,
        )
        keepalive.start()
        print(f"[OpenPhone] Screen keepalive active (interval: {interval}s)")

        try:
            _run_interactive_loop(
                args=run_args,
                controller=controller,
                executor=executor,
                exec_agent=exec_agent,
                eval_agent=eval_agent,
                planner=planner,
                evaluator=evaluator,
            )
        finally:
            keepalive.stop()

        return {"success": True}

    except ConnectionError as e:
        return {"success": False, "error": {"code": "CONNECTION_ERROR", "message": str(e)}}
    except KeyboardInterrupt:
        return {"success": True, "message": "Daemon stopped by user."}
    except Exception as e:
        return {"success": False, "error": {"code": "DAEMON_ERROR", "message": str(e)}}


# ---------------------------------------------------------------------------
# learn
# ---------------------------------------------------------------------------

def cmd_learn(args: argparse.Namespace) -> dict:
    """Record a human demonstration and extract navigation lessons."""
    _run_learn_mode = _get_run_phoneclaw_attr("_run_learn_mode")
    IOSConnection = _get_phoneclaw_attr("connection", "IOSConnection")
    ExperienceLog = _get_phoneclaw_attr("experience", "ExperienceLog")

    run_args = _build_run_namespace(vars(args))

    try:
        conn = IOSConnection(wda_url=run_args.wda_url)
        if not conn.is_wda_ready():
            return {"success": False, "error": {"code": "WDA_NOT_READY",
                    "message": f"WebDriverAgent not ready at {run_args.wda_url}"}}

        ok, session_id = conn.start_wda_session()
        if not ok:
            return {"success": False, "error": {"code": "WDA_SESSION_FAILED",
                    "message": f"Failed to start WDA session: {session_id}"}}

        exec_agent, _, _, _ = _setup_agents(run_args)

        learn_args = _build_run_namespace({
            **vars(run_args),
            "learn_app": args.app or "unknown",
            "learn_describe": args.describe or f"Demonstration on {args.app or 'unknown'}",
            "learn_poll": args.poll,
            "learn_threshold": args.threshold,
            "learn_duration": args.duration,
            "learn_dir": args.demo_dir,
            "no_analyse": args.no_analyse,
        })

        _run_learn_mode(
            args=learn_args,
            wda_url=learn_args.wda_url,
            session_id=session_id,
            exec_agent=exec_agent,
            experience=ExperienceLog(log_path=learn_args.experience_path),
        )

        return {"success": True, "app": learn_args.learn_app}

    except ConnectionError as e:
        return {"success": False, "error": {"code": "CONNECTION_ERROR", "message": str(e)}}
    except Exception as e:
        return {"success": False, "error": {"code": "LEARN_ERROR", "message": str(e)}}


# ---------------------------------------------------------------------------
# Subcommand registration
# ---------------------------------------------------------------------------

def register_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register autonomous-mode subcommands on the given subparsers."""

    def _add_shared_args(p):
        p.add_argument("--wda-url", default=os.getenv("WDA_URL", "http://localhost:8100"),
                       help="WebDriverAgent URL")
        p.add_argument("--openrouter", action="store_true",
                       default=bool(os.getenv("OPENROUTER_API_KEY")),
                       help="Use OpenRouter as VLM backend")
        p.add_argument("--openrouter-api-key", default=os.getenv("OPENROUTER_API_KEY", ""))
        p.add_argument("--openrouter-base-url", default=OPENROUTER_BASE_URL)
        p.add_argument("--openrouter-site-url", default=os.getenv("OPENROUTER_SITE_URL", "None"))
        p.add_argument("--openrouter-app-title", default=os.getenv("OPENROUTER_APP_TITLE", "PhoneClaw"))
        p.add_argument("--model-name", default=os.getenv("OPENROUTER_MODEL",
                       os.getenv("MODEL_NAME", "z-ai/glm-4.6v")))
        p.add_argument("--api-base", default=os.getenv("API_BASE", "http://localhost:8002/v1"))
        p.add_argument("--api-key", default=os.getenv("API_KEY", "EMPTY"))
        p.add_argument("--agent-type", default=os.getenv("AGENT_TYPE", "OpenAIAgent"),
                       choices=["OpenAIAgent", "QwenVLAgent"])
        p.add_argument("--eval-model-name", default=os.getenv("EVAL_OPENROUTER_MODEL",
                       os.getenv("EVAL_MODEL_NAME", None)))
        p.add_argument("--eval-api-base", default=os.getenv("EVAL_API_BASE", None))
        p.add_argument("--eval-api-key", default=os.getenv("EVAL_API_KEY", None))
        p.add_argument("--max-rounds", type=int, default=100)
        p.add_argument("--max-fix-retries", type=int, default=3)
        p.add_argument("--request-interval", type=float, default=2.0)
        p.add_argument("--no-skip-failed", action="store_true")
        p.add_argument("--keepalive-interval", type=float, default=0)
        p.add_argument("--no-memory", action="store_true")
        p.add_argument("--no-experience", action="store_true")
        p.add_argument("--memory-path", default=None)
        p.add_argument("--experience-path", default=None)

    # ---- run ----
    p_run = subparsers.add_parser("run", help="Execute a task autonomously via Ralph Loop")
    p_run.add_argument("task", nargs="?", help="Task description")
    _add_shared_args(p_run)
    p_run.add_argument("--task-dir", default=None, help="Directory for task logs")
    p_run.add_argument("--resume", action="store_true", help="Resume from saved state")
    p_run.set_defaults(func=cmd_run)

    # ---- daemon ----
    p_daemon = subparsers.add_parser("daemon", help="Start interactive daemon mode")
    _add_shared_args(p_daemon)
    p_daemon.set_defaults(func=cmd_daemon)

    # ---- learn ----
    p_learn = subparsers.add_parser("learn", help="Record a demo and extract navigation lessons")
    p_learn.add_argument("app", nargs="?", help="App name to learn about")
    p_learn.add_argument("--describe", default=None, help="Task description for the demo")
    p_learn.add_argument("--poll", type=float, default=0.12, help="Screenshot poll interval in seconds")
    p_learn.add_argument("--threshold", type=float, default=0.003, help="Screen change detection threshold")
    p_learn.add_argument("--duration", type=float, default=None, help="Recording duration (seconds)")
    p_learn.add_argument("--demo-dir", default=None, help="Directory for demo recordings")
    p_learn.add_argument("--no-analyse", action="store_true", help="Skip VLM analysis after recording")
    _add_shared_args(p_learn)
    p_learn.set_defaults(func=cmd_learn)
