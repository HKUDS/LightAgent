"""Memory management commands for the OpenPhone CLI.

Usage:
    openphone memory show
    openphone memory list [--app <name>] [--limit N]
    openphone memory query <question>
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

# Ensure project root is on sys.path
_project_root = Path(__file__).parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))


def _get_user_memory():
    """Lazy import UserMemory from PhoneClaw.memory."""
    from PhoneClaw.memory import UserMemory
    return UserMemory


def _get_experience_log():
    """Lazy import ExperienceLog from PhoneClaw.experience."""
    from PhoneClaw.experience import ExperienceLog
    return ExperienceLog


# ---------------------------------------------------------------------------
# memory show
# ---------------------------------------------------------------------------

def cmd_memory_show(args: argparse.Namespace) -> dict:
    """Display user profile summary."""
    UserMemory = _get_user_memory()
    memory = UserMemory()
    data = memory.data
    stats = data["stats"]
    profile = data["profile"]

    return {
        "success": True,
        "profile_path": str(memory.get_profile_path()),
        "stats": {
            "total_sessions": stats["total_sessions"],
            "total_tasks": stats["total_tasks"],
            "completed_tasks": stats["completed_tasks"],
            "failed_tasks": stats["failed_tasks"],
        },
        "profile": {
            "inferred_name": profile.get("inferred_name"),
            "inferred_location": profile.get("inferred_location"),
            "primary_language": profile.get("primary_language"),
        },
        "top_apps": sorted(
            data["app_usage"].items(),
            key=lambda x: x[1]["count"],
            reverse=True,
        )[:10],
        "insight_count": len(data["insights"]),
        "recent_insights": data["insights"][-10:],
        "recent_tasks": data["task_history"][-5:],
    }


# ---------------------------------------------------------------------------
# memory list
# ---------------------------------------------------------------------------

def cmd_memory_list(args: argparse.Namespace) -> dict:
    """List experience lessons, optionally filtered by app."""
    ExperienceLog = _get_experience_log()
    exp = ExperienceLog()
    lessons = exp.data["lessons"]

    app_filter: Optional[str] = getattr(args, "app", None)
    limit: int = getattr(args, "limit", 50)

    if app_filter:
        lessons = [l for l in lessons if l.get("app", "").lower() == app_filter.lower()]

    lessons = sorted(
        lessons,
        key=lambda x: (
            {"high": 3, "medium": 2, "low": 1}.get(x.get("confidence", "low"), 1),
            x.get("reinforced", 1),
        ),
        reverse=True,
    )[:limit]

    return {
        "success": True,
        "total_lessons": exp.data["stats"]["total_lessons"],
        "tasks_processed": exp.data["stats"]["tasks_processed"],
        "app_filter": app_filter,
        "lessons": [
            {
                "app": l.get("app", "general"),
                "type": l.get("lesson_type"),
                "confidence": l.get("confidence"),
                "reinforced": l.get("reinforced", 1),
                "description": l.get("description"),
            }
            for l in lessons
        ],
    }


# ---------------------------------------------------------------------------
# memory query
# ---------------------------------------------------------------------------

def cmd_memory_query(args: argparse.Namespace) -> dict:
    """Search memory for relevant information (text match against insights)."""
    UserMemory = _get_user_memory()
    ExperienceLog = _get_experience_log()

    question: str = args.question.lower()
    memory = UserMemory()
    exp = ExperienceLog()

    # Search insights
    matched_insights = []
    for insight in memory.data["insights"]:
        text = insight.get("text", "").lower()
        if any(word in text for word in question.split()):
            matched_insights.append(insight)

    # Search experience lessons
    matched_lessons = []
    for lesson in exp.data["lessons"]:
        desc = lesson.get("description", "").lower()
        app = lesson.get("app", "").lower()
        if any(word in desc or word in app for word in question.split()):
            matched_lessons.append(lesson)

    return {
        "success": True,
        "question": args.question,
        "matched_insights": [
            {"text": i.get("text"), "confidence": i.get("confidence"), "source": i.get("source_task_id")}
            for i in matched_insights[:10]
        ],
        "matched_lessons": [
            {
                "app": l.get("app"),
                "type": l.get("lesson_type"),
                "description": l.get("description"),
                "confidence": l.get("confidence"),
            }
            for l in matched_lessons[:10]
        ],
    }


# ---------------------------------------------------------------------------
# Subcommand registration
# ---------------------------------------------------------------------------

def register_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register memory subcommands on the given subparsers."""
    p_memory = subparsers.add_parser("memory", help="Manage user memory and experience log")
    mem_subs = p_memory.add_subparsers(dest="memory_action", help="Memory action")

    p_show = mem_subs.add_parser("show", help="Show user profile summary")
    p_show.set_defaults(func=cmd_memory_show)

    p_list = mem_subs.add_parser("list", help="List experience lessons")
    p_list.add_argument("--app", help="Filter by app name")
    p_list.add_argument("--limit", type=int, default=50, help="Max lessons to show")
    p_list.set_defaults(func=cmd_memory_list)

    p_query = mem_subs.add_parser("query", help="Search memory for relevant information")
    p_query.add_argument("question", help="Search query")
    p_query.set_defaults(func=cmd_memory_query)
