"""Session and persistent memory for phonecli daemon mode.

Two memory tiers with clear separation:

  DialogueMemory  – in-memory, session-scoped cache
  UserMemory      – on-disk, cross-session, app-map-aware profile

DialogueMemory
  Fast cache for "what was just asked?" — eliminates repeated VLM calls
  on the same question within one daemon session.

UserMemory
  Accumulates task history, app usage stats, and operation knowledge across
  sessions.  App-map-aware: stores (task, app, op_id) triples so future
  sessions can suggest an operation ID directly, bypassing LLM map-task.
"""

from __future__ import annotations

import json
import os
import re
import time as _time_module
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# DialogueMemory — session-scoped, in-memory
# ---------------------------------------------------------------------------

@dataclass
class DialogueEntry:
    task: str
    answer: str
    app_name: str
    op_id: str
    timestamp: float


class DialogueMemory:
    """In-memory cache of completed tasks within one daemon session.

    Eliminates repeated API calls for the same question asked twice.
    """

    def __init__(self, max_entries: int = 50):
        self._entries: list[DialogueEntry] = []
        self._max_entries = max_entries

    def record(self, task: str, answer: str, app_name: str = "",
               op_id: str = ""):
        """Store a completed task and its answer."""
        entry = DialogueEntry(
            task=task,
            answer=answer,
            app_name=app_name,
            op_id=op_id,
            timestamp=_time_module.time(),
        )
        self._entries.append(entry)
        if len(self._entries) > self._max_entries:
            self._entries = self._entries[-self._max_entries:]

    def query(self, task: str) -> Optional[str]:
        """Check if *task* was already answered in this session.

        Uses token-overlap fuzzy matching (case-insensitive).
        """
        task_lower = task.lower()
        task_tokens = set(re.findall(r'\w+', task_lower))

        best_score = 0.0
        best_answer: Optional[str] = None

        for entry in reversed(self._entries):
            entry_tokens = set(re.findall(r'\w+', entry.task.lower()))
            if not entry_tokens or not task_tokens:
                continue
            overlap = len(task_tokens & entry_tokens)
            union = len(task_tokens | entry_tokens)
            score = overlap / union if union > 0 else 0

            # Exact match bonus
            if task_lower == entry.task.lower():
                score = 1.0

            if score >= 0.55 and score > best_score:
                best_score = score
                best_answer = entry.answer

        return best_answer if best_score >= 0.55 else None

    def suggest_op(self, task: str, app_name: str = None) -> tuple:
        """Check if a similar task in this session used a macro operation.

        Returns (op_id, score) or (None, 0).
        """
        task_lower = task.lower()
        task_tokens = set(re.findall(r'\w+', task_lower))
        best_score = 0.0
        best_op = None

        for entry in reversed(self._entries):
            if not entry.op_id:
                continue
            if app_name and entry.app_name.lower() != app_name.lower():
                continue

            entry_tokens = set(re.findall(r'\w+', entry.task.lower()))
            if not entry_tokens or not task_tokens:
                continue

            overlap = len(task_tokens & entry_tokens)
            union = len(task_tokens | entry_tokens)
            score = overlap / union if union > 0 else 0

            if task_lower == entry.task.lower():
                score = 1.0

            if score > best_score:
                best_score = score
                best_op = entry.op_id

        return best_op, best_score

    def get_hints(self, app_name: str, task: str) -> str:
        """Return formatted hints from recent entries for prompt injection.

        Selects entries matching the same app_name or with keyword overlap.
        Returns empty string when no relevant entries exist.
        """
        if not self._entries:
            return ""

        task_lower = task.lower()
        task_tokens = set(re.findall(r'\w+', task_lower))

        scored: list[tuple[float, DialogueEntry]] = []
        for entry in self._entries:
            score = 0.0
            # Same app bonus
            if app_name and entry.app_name.lower() == app_name.lower():
                score += 3.0
            # Keyword overlap
            entry_tokens = set(re.findall(r'\w+', entry.task.lower()))
            if entry_tokens and task_tokens:
                overlap = len(task_tokens & entry_tokens)
                score += overlap * 1.5
            # Recent bonus (more recent = higher score)
            age_hours = (_time_module.time() - entry.timestamp) / 3600.0
            score += max(0, 2.0 - age_hours)

            if score >= 1.0:
                scored.append((score, entry))

        if not scored:
            return ""

        scored.sort(key=lambda x: x[0], reverse=True)
        top = [e for _, e in scored[:5]]

        lines = ["Previously completed tasks in this session:"]
        for e in top:
            op_tag = f" [via {e.op_id}]" if e.op_id else ""
            lines.append(f"  - Q: {e.task}{op_tag}")
            lines.append(f"    A: {e.answer[:120]}")
        return "\n".join(lines)

    def clear(self):
        """Reset all entries (for 'forget' command)."""
        self._entries.clear()

    def __len__(self):
        return len(self._entries)


# ---------------------------------------------------------------------------
# UserMemory — on-disk, cross-session, app-map-aware
# ---------------------------------------------------------------------------

DEFAULT_PROFILE_DIR = Path.home() / ".phonecli"
DEFAULT_PROFILE_PATH = DEFAULT_PROFILE_DIR / "user_profile.json"
SCHEMA_VERSION = 1
MAX_TASK_HISTORY = 200
MAX_INSIGHTS = 100


class UserMemory:
    """Persistent user profile and task history.

    Stores (task, app_name, op_id) triples so future sessions can bypass
    LLM map-task entirely for previously-executed operations.
    """

    def __init__(self, profile_path: Optional[str] = None):
        self.path = Path(profile_path or DEFAULT_PROFILE_PATH)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.data = self._load()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _load(self) -> dict:
        if self.path.exists():
            try:
                with open(self.path, encoding="utf-8") as f:
                    raw = json.load(f)
                if raw.get("schema_version", 0) < SCHEMA_VERSION:
                    raw = self._migrate(raw)
                return raw
            except Exception as exc:
                backup = str(self.path) + f".corrupt.{int(datetime.now().timestamp())}"
                try:
                    os.rename(str(self.path), backup)
                    print(f"[Memory] Corrupt profile backed up to: {backup}")
                except Exception:
                    pass
                print(f"[Memory] Warning: could not load profile ({exc}). Starting fresh.")
        return self._empty_profile()

    def save(self):
        self.data["last_updated"] = datetime.now().isoformat()
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def _empty_profile(self) -> dict:
        return {
            "schema_version": SCHEMA_VERSION,
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "stats": {
                "total_sessions": 0,
                "total_tasks": 0,
                "completed_tasks": 0,
                "failed_tasks": 0,
            },
            "profile": {
                "inferred_name": None,
                "inferred_location": None,
                "notes": [],
            },
            "app_usage": {},
            "task_history": [],
            "insights": [],
            "op_knowledge": {},
        }

    def _migrate(self, old: dict) -> dict:
        fresh = self._empty_profile()
        for k in fresh:
            if k in old:
                fresh[k] = old[k]
        fresh["schema_version"] = SCHEMA_VERSION
        if "op_knowledge" not in fresh:
            fresh["op_knowledge"] = {}
        return fresh

    # ------------------------------------------------------------------
    # Session
    # ------------------------------------------------------------------

    def start_session(self):
        self.data["stats"]["total_sessions"] += 1
        self.save()

    def session_banner(self) -> str:
        stats = self.data["stats"]
        p = self.data["profile"]
        parts = [
            f"[Memory] Profile: {self.path}",
            f"[Memory] Sessions: {stats['total_sessions']}  |  "
            f"Tasks: {stats['completed_tasks']} completed / "
            f"{stats['failed_tasks']} failed  |  "
            f"Insights: {len(self.data['insights'])}",
        ]
        if p.get("inferred_name"):
            parts.append(f"[Memory] User: {p['inferred_name']}")
        return "\n".join(parts)

    # ------------------------------------------------------------------
    # Task recording (app-map-aware)
    # ------------------------------------------------------------------

    def record_task(
        self,
        task: str,
        status: str,
        final_answer: str,
        app_name: str = "",
        op_id: str = "",
        rounds: int = 0,
        duration_seconds: float = 0,
    ) -> int:
        """Record a completed task and update counters.

        Returns 1-based task ID.
        """
        stats = self.data["stats"]
        stats["total_tasks"] += 1
        if status == "completed":
            stats["completed_tasks"] += 1
        else:
            stats["failed_tasks"] += 1

        # Per-app usage
        now = datetime.now().isoformat()
        if app_name:
            entry = self.data["app_usage"].setdefault(
                app_name, {"count": 0, "last_used": None}
            )
            entry["count"] += 1
            entry["last_used"] = now

        # Operation knowledge
        if op_id and app_name:
            op_entry = self.data["op_knowledge"].setdefault(op_id, {
                "description": task[:80],
                "app": app_name,
                "times_used": 0,
                "avg_duration": 0,
            })
            prev_times = op_entry["times_used"]
            prev_avg = op_entry["avg_duration"]
            op_entry["times_used"] += 1
            op_entry["avg_duration"] = round(
                (prev_avg * prev_times + duration_seconds) / (prev_times + 1), 1
            )

        # Task history
        history: list = self.data["task_history"]
        task_id = len(history) + 1
        history.append({
            "id": task_id,
            "timestamp": now,
            "task": task,
            "status": status,
            "final_answer": final_answer,
            "app_name": app_name,
            "op_id": op_id,
            "rounds": rounds,
            "duration_seconds": round(duration_seconds, 1),
        })

        if len(history) > MAX_TASK_HISTORY:
            self.data["task_history"] = history[-MAX_TASK_HISTORY:]

        self.save()
        return task_id

    # ------------------------------------------------------------------
    # Memory-first retrieval
    # ------------------------------------------------------------------

    def query(self, task: str, app_name: str = None) -> tuple:
        """Check if task was previously completed with a known answer.

        Returns (can_answer, answer).
        """
        task_lower = task.lower()
        task_tokens = set(re.findall(r'\w+', task_lower))

        # 1. Exact task match in history
        for entry in reversed(self.data["task_history"]):
            if entry.get("status") == "completed" and entry.get("final_answer"):
                entry_task = entry.get("task", "")
                if entry_task.lower() == task_lower:
                    return True, entry["final_answer"]

        # 2. High-overlap task in history
        for entry in reversed(self.data["task_history"]):
            if entry.get("status") == "completed" and entry.get("final_answer"):
                entry_tokens = set(re.findall(r'\w+', entry.get("task", "").lower()))
                if not entry_tokens or not task_tokens:
                    continue
                overlap = len(task_tokens & entry_tokens)
                union = len(task_tokens | entry_tokens)
                if union > 0 and overlap / union >= 0.7:
                    return True, entry["final_answer"]

        # 3. App-aware: same app + high keyword overlap
        if app_name:
            for entry in reversed(self.data["task_history"]):
                if (entry.get("status") == "completed"
                        and entry.get("final_answer")
                        and entry.get("app_name", "").lower() == app_name.lower()):
                    entry_tokens = set(re.findall(
                        r'\w+', entry.get("task", "").lower()
                    ))
                    if not entry_tokens or not task_tokens:
                        continue
                    overlap = len(task_tokens & entry_tokens)
                    union = len(task_tokens | entry_tokens)
                    if union > 0 and overlap / union >= 0.7:
                        return True, entry["final_answer"]

        return False, None

    # ------------------------------------------------------------------
    # Macro-aware retrieval — task → op_id mapping
    # ------------------------------------------------------------------

    def suggest_op(self, task: str, app_name: str = None) -> tuple:
        """Check if a similar task was previously completed via a macro operation.

        This enables bypassing the LLM map-task call entirely — if we know
        that "turn on wifi" → op_wifi_on, we can go straight to macro replay.

        Returns:
            (op_id, description, score) if a match is found, else (None, None, 0).
        """
        task_lower = task.lower()
        task_tokens = set(re.findall(r'\w+', task_lower))
        best_score = 0.0
        best_entry = None

        for entry in reversed(self.data["task_history"]):
            if entry.get("status") != "completed":
                continue
            op_id = entry.get("op_id", "")
            if not op_id:
                continue

            # App filter: only consider entries from the same app
            if app_name and entry.get("app_name", "").lower() != app_name.lower():
                continue

            entry_task = entry.get("task", "")
            entry_tokens = set(re.findall(r'\w+', entry_task.lower()))

            if not entry_tokens or not task_tokens:
                continue

            overlap = len(task_tokens & entry_tokens)
            union = len(task_tokens | entry_tokens)
            score = overlap / union if union > 0 else 0

            # Exact match bonus
            if task_lower == entry_task.lower():
                score = 1.0

            # Bonus for frequently-used operations
            op_info = self.data.get("op_knowledge", {}).get(op_id, {})
            times_used = op_info.get("times_used", 0)
            score += min(times_used * 0.02, 0.15)  # up to +0.15 for proven ops

            if score > best_score:
                best_score = score
                best_entry = entry

        if best_entry and best_score >= 0.45:
            op_id = best_entry["op_id"]
            op_info = self.data.get("op_knowledge", {}).get(op_id, {})
            desc = op_info.get("description", best_entry.get("task", ""))
            return op_id, desc, best_score

        return None, None, 0

    def get_op_hints(self, task: str, app_name: str = None) -> str:
        """Return formatted hints about which operations might match this task.

        Used to inject into the LLM map-task prompt so the LLM can leverage
        past experience.
        """
        if not app_name:
            return ""

        task_lower = task.lower()
        task_tokens = set(re.findall(r'\w+', task_lower))
        scored: list[tuple[float, dict]] = []

        for entry in self.data["task_history"]:
            if not entry.get("op_id"):
                continue
            if entry.get("app_name", "").lower() != app_name.lower():
                continue
            if entry.get("status") != "completed":
                continue

            entry_tokens = set(re.findall(r'\w+', entry.get("task", "").lower()))
            if not entry_tokens or not task_tokens:
                continue

            overlap = len(task_tokens & entry_tokens)
            if overlap >= 1:
                op_id = entry["op_id"]
                op_info = self.data.get("op_knowledge", {}).get(op_id, {})
                score = overlap + op_info.get("times_used", 0) * 0.5
                scored.append((score, entry))

        if not scored:
            return ""

        scored.sort(key=lambda x: x[0], reverse=True)
        seen_ops: set = set()
        lines = ["Past macro operations for similar tasks:"]
        for _, entry in scored[:5]:
            op_id = entry["op_id"]
            if op_id in seen_ops:
                continue
            seen_ops.add(op_id)
            lines.append(f"  - Task: \"{entry['task'][:80]}\" → used {op_id}")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Planner context
    # ------------------------------------------------------------------

    def get_planner_context(self) -> str:
        """Return formatted context string for prompt injection.

        Includes known facts, app usage, recent task history.
        Returns empty string if profile has no useful information.
        """
        p = self.data["profile"]
        lines: list[str] = []

        if p.get("inferred_name"):
            lines.append(f"- Name: {p['inferred_name']}")
        if p.get("inferred_location"):
            lines.append(f"- Location: {p['inferred_location']}")

        top_apps = sorted(
            self.data["app_usage"].items(),
            key=lambda x: x[1]["count"],
            reverse=True,
        )[:6]
        if top_apps:
            app_str = ", ".join(f"{a} ({v['count']}x)" for a, v in top_apps)
            lines.append(f"- Frequently used apps: {app_str}")

        recent_insights = self.data["insights"][-10:]
        if recent_insights:
            lines.append("- Known facts:")
            for ins in recent_insights:
                lines.append(f"  - {ins['text']}")

        recent_tasks = self.data["task_history"][-4:]
        if recent_tasks:
            lines.append("- Recent tasks:")
            for t in recent_tasks:
                icon = "OK" if t["status"] == "completed" else "FAIL"
                lines.append(f"  [{icon}] {t['task'][:80]}")

        if not lines:
            return ""

        return "## User Profile (from memory)\n" + "\n".join(lines)

    # ------------------------------------------------------------------
    # Insight extraction (VLM-powered, optional)
    # ------------------------------------------------------------------

    def extract_insights(self, task: str, final_answer: str,
                         task_id: int, agent) -> list:
        """Call VLM to extract user-relevant facts from a completed task.

        The agent must implement: agent.act(messages: list[dict]) -> str
        """
        from phonecli.prompts import MEMORY_EXTRACT_PROMPT

        user_content = MEMORY_EXTRACT_PROMPT.format(
            task=task, answer=final_answer or ""
        )
        existing = self._existing_summary()
        if existing:
            user_content += f"\n\nAlready known about user:\n{existing}"

        try:
            from phonecli.llm_client import text_completion
            response = text_completion(
                system_prompt="Output a JSON array of insight strings.",
                user_prompt=user_content,
                max_tokens=512, temperature=0.0,
            )
            raw_insights = self._parse_insights(response)
            added: list = []
            for text in raw_insights:
                if self._add_insight(text, task_id):
                    added.append(text)
            if added:
                print(f"[Memory] +{len(added)} new insight(s)")
                for ins in added:
                    print(f"  - {ins}")
            return added
        except Exception as exc:
            print(f"[Memory] Could not extract insights: {exc}")
            return []

    def _add_insight(self, text: str, source_task_id: int) -> bool:
        """Add an insight if not a duplicate. Returns True if new."""
        text = text.strip()
        if not text or len(text) < 7:
            return False

        # Simple fuzzy dedup
        for existing in self.data["insights"]:
            exist_words = set(re.findall(r'\w+', existing["text"].lower()))
            new_words = set(re.findall(r'\w+', text.lower()))
            if not exist_words or not new_words:
                continue
            overlap = len(exist_words & new_words)
            union = len(exist_words | new_words)
            if union > 0 and overlap / union >= 0.65:
                existing["reinforced"] = existing.get("reinforced", 1) + 1
                existing["last_seen"] = datetime.now().isoformat()
                self.save()
                return False

        self.data["insights"].append({
            "text": text,
            "confidence": "medium",
            "source_task_id": source_task_id,
            "timestamp": datetime.now().isoformat(),
            "reinforced": 1,
        })

        if len(self.data["insights"]) > MAX_INSIGHTS:
            self.data["insights"] = self.data["insights"][-MAX_INSIGHTS:]

        self.save()
        return True

    def _parse_insights(self, response: str) -> list:
        """Parse VLM response into insight strings."""
        try:
            start = response.index("[")
            end = response.rindex("]") + 1
            items = json.loads(response[start:end])
            return [str(item).strip() for item in items if str(item).strip()]
        except (ValueError, json.JSONDecodeError):
            pass

        lines = []
        for line in response.splitlines():
            stripped = re.sub(r"^[\s\-\*\d\.\)]+", "", line).strip()
            if len(stripped) > 8:
                lines.append(stripped)
        return lines[:10]

    def _existing_summary(self) -> str:
        """Compact summary of already-known facts."""
        p = self.data["profile"]
        parts = []
        if p.get("inferred_name"):
            parts.append(f"User: {p['inferred_name']}")
        if self.data["insights"]:
            recent = self.data["insights"][-6:]
            parts.append(
                "Recent:\n" + "\n".join(f"  - {i['text']}" for i in recent)
            )
        return "\n".join(parts) if parts else ""

    # ------------------------------------------------------------------
    # Display
    # ------------------------------------------------------------------

    def print_summary(self):
        """Pretty-print the profile to terminal."""
        data = self.data
        stats = data["stats"]
        profile = data["profile"]
        BANNER = "=" * 60

        print(f"\n{BANNER}")
        print(f"  User Profile  —  {self.path}")
        print(BANNER)
        print(f"  Sessions     : {stats['total_sessions']}")
        print(f"  Tasks        : {stats['total_tasks']}  "
              f"(OK {stats['completed_tasks']}  FAIL {stats['failed_tasks']})")
        print(f"  Insights     : {len(data['insights'])}")

        if profile.get("inferred_name"):
            print(f"  Name         : {profile['inferred_name']}")
        if profile.get("inferred_location"):
            print(f"  Location     : {profile['inferred_location']}")

        top_apps = sorted(
            data["app_usage"].items(),
            key=lambda x: x[1]["count"],
            reverse=True,
        )[:8]
        if top_apps:
            print("\n  App usage:")
            for app, v in top_apps:
                print(f"    {app:<20} {v['count']}x  (last: {v['last_used'][:10]})")

        if data["op_knowledge"]:
            print("\n  Operations:")
            for op_id, v in sorted(
                data["op_knowledge"].items(),
                key=lambda x: x[1]["times_used"],
                reverse=True,
            )[:8]:
                print(f"    {op_id:<20} {v['times_used']}x  "
                      f"({v.get('avg_duration', 0):.0f}s avg)")

        if data["insights"]:
            print("\n  Insights:")
            for ins in data["insights"][-12:]:
                print(f"    - {ins['text']}")

        if data["task_history"]:
            print("\n  Recent tasks:")
            for t in data["task_history"][-8:]:
                icon = "OK" if t["status"] == "completed" else "FAIL"
                ts = t["timestamp"][:16]
                ans = f"  -> {t['final_answer'][:50]}" if t.get("final_answer") else ""
                op = f" [{t['op_id']}]" if t.get("op_id") else ""
                print(f"    {icon} [{ts}] {t['task'][:60]}{op}{ans}")

        print(BANNER + "\n")

    def clear(self):
        """Reset profile to empty."""
        self.data = self._empty_profile()
        self.save()
        print("[Memory] Profile cleared.")

    def get_profile_path(self) -> str:
        return str(self.path)
