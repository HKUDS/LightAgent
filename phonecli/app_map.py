"""App map data structures: load YAML, match screens, build operation catalogs.

Macro format uses platform-agnostic abstract actions (not shell commands):

  {"action": "launch", "bundle_id": "com.apple.Preferences", "wait": 2.0}
  {"action": "tap", "x": 200, "y": 400, "wait": 1.0}
  {"action": "swipe", "x1": 100, "y1": 500, "x2": 100, "y2": 200, "duration": 400, "wait": 0.5}
"""

import re
from dataclasses import dataclass, field
from typing import Optional

import yaml


@dataclass
class ScreenElement:
    text: str
    center: tuple[float, float]  # normalized [0, 1]
    leads_to: Optional[str] = None
    found_at_scroll: int = 0
    fixed: bool = False
    aliases: list[str] = field(default_factory=list)  # e.g. ["WiFi", "wireless", "无线"]
    semantic_type: str = ""  # "toggle", "button", "network", "input", "tab", "label", "link"


@dataclass
class Screen:
    id: str
    elements: list[ScreenElement] = field(default_factory=list)
    description: str = ""  # human-readable: "Wi-Fi settings: toggle at top, networks below"
    scrollable: bool = False
    scroll_direction: str = ""  # "vertical" | "horizontal"


@dataclass
class Operation:
    id: str
    description: str
    macro: list[dict]  # list of abstract action dicts
    type: str  # "NAV" or "ACT"


class AppMap:
    """Loads and queries a YAML app map file."""

    def __init__(self, map_path: str):
        try:
            with open(map_path, "r") as f:
                self.data = yaml.safe_load(f)
        except (FileNotFoundError, yaml.YAMLError) as e:
            raise ValueError(f"Failed to load app map '{map_path}': {e}") from e
        self.map_path = map_path
        self.app_name = self.data.get("app", "Unknown")
        self.package = self.data.get("package", "")
        self.screen_w = self.data.get("screen_w", 390)
        self.screen_h = self.data.get("screen_h", 844)

        # App-level metadata
        self.launch_behavior = self.data.get("launch_behavior", "always_home")
        self.common_tasks: list[str] = self.data.get("common_tasks", [])
        self.known_limitations: list[str] = self.data.get("known_limitations", [])

        self.screens: list[Screen] = []
        for s in self.data.get("screens", []):
            elements = []
            for e in s.get("elements", []):
                elements.append(ScreenElement(
                    text=e["text"],
                    center=tuple(e["center"]),
                    leads_to=e.get("leads_to"),
                    found_at_scroll=e.get("found_at_scroll", 0),
                    fixed=e.get("fixed", False),
                    aliases=e.get("aliases", []),
                    semantic_type=e.get("semantic_type", ""),
                ))
            self.screens.append(Screen(
                id=s["id"],
                elements=elements,
                description=s.get("description", ""),
                scrollable=s.get("scrollable", False),
                scroll_direction=s.get("scroll_direction", ""),
            ))

        self._macros = self.data.get("screen_macros", {})

    def get_screen(self, screen_id: str) -> Optional[Screen]:
        for s in self.screens:
            if s.id == screen_id:
                return s
        return None

    def identify_current_screen(self, xml_str: str) -> tuple:
        """Identify which map screen best matches the given XML source.

        Returns (screen_id, confidence) where confidence is 0.0–1.0.
        Returns (None, 0) if no good match found.
        """
        xml_texts = set()
        interactive_types = [
            'XCUIElementTypeButton', 'XCUIElementTypeCell',
            'XCUIElementTypeTextField', 'XCUIElementTypeSecureTextField',
            'XCUIElementTypeSearchField', 'XCUIElementTypeSwitch',
            'XCUIElementTypeTab', 'XCUIElementTypeLink',
            'XCUIElementTypeStaticText', 'XCUIElementTypeImage',
            'XCUIElementTypeIcon',
        ]
        for itype in interactive_types:
            for tag_match in re.finditer(rf'<{itype}\b([^>]*?)/>', xml_str):
                attrs = tag_match.group(0)
                label_match = re.search(r'label="([^"]*)"', attrs)
                name_match = re.search(r'name="([^"]*)"', attrs)
                text = label_match.group(1) if label_match else ""
                if not text and name_match:
                    text = name_match.group(1)
                text = text.strip()
                if text and len(text) > 1:
                    xml_texts.add(text)

        if not xml_texts:
            return None, 0.0

        best_id, best_overlap, best_coverage = None, 0, 0.0
        for screen in self.screens:
            screen_texts = {e.text for e in screen.elements}
            if not screen_texts:
                continue
            overlap = len(xml_texts & screen_texts)
            coverage = overlap / len(screen_texts)
            # Preference: more absolute matches = more specific identification.
            # Require ≥50% coverage to filter out irrelevant screens.
            if coverage >= 0.5 and overlap > best_overlap:
                best_overlap, best_id, best_coverage = overlap, screen.id, coverage

        if best_id is None:
            return None, best_coverage
        return best_id, best_coverage

    def find_relative_macro(self, from_id: str, to_id: str) -> list:
        """Return the relative action steps to go from from_screen to to_screen.

        Uses the full-path macros stored in screen_macros. Strips the common
        prefix between the two paths, keeping only the steps unique to to_screen.
        If the screens share no common prefix (e.g. from was reached via VLM),
        returns the full path for to_screen.
        """
        from_path = self._macros.get(from_id, [])
        to_path = self._macros.get(to_id, [])
        if not to_path:
            return []
        if not from_path:
            return list(to_path)

        # Strip common prefix
        i = 0
        while i < min(len(from_path), len(to_path)):
            if from_path[i] != to_path[i]:
                break
            i += 1
        return list(to_path[i:])

    def get_nav_targets(self, from_screen_id: str) -> list[str]:
        """Return navigation target names reachable from a given screen.

        Includes element text and the first alias (if any).
        The VLM can use macro(\"TargetName\") with either the text or an alias.
        """
        targets = []
        screen = self.get_screen(from_screen_id)
        if screen:
            for e in screen.elements:
                if e.leads_to:
                    label = e.text
                    if e.aliases:
                        label += f" ({e.aliases[0]})"
                    targets.append(label)
        return targets

    def build_operations(self) -> dict[str, Operation]:
        """Build operations catalog by traversing the screen graph."""
        ops: dict[str, Operation] = {}
        visited_screens: set[str] = set()
        visited_ops: set[str] = set()

        def _skip(text: str) -> bool:
            t = text.lower()
            skips = [
                "profile picture", "navigate up", "more options",
                "dismiss", "clear", "learn more", "back", "cancel",
                "no unused", "no recent", "no nearby",
                "google account", "manage your google",
            ]
            return any(s in t for s in skips) or len(text.strip()) <= 1

        def _op_id(texts: list[str]) -> str:
            clean = "".join(c if c.isalnum() else "_" for c in "_".join(texts).lower())
            return clean.strip("_")[:60]

        def _explore(screen_id: str, prefix_texts: list[str], depth: int, max_depth: int = 6):
            if depth > max_depth or screen_id in visited_screens:
                return
            visited_screens.add(screen_id)
            screen = self.get_screen(screen_id)
            if not screen:
                return

            base_macro = list(self._macros.get(screen_id, []))
            for e in screen.elements:
                if _skip(e.text) or not e.text:
                    continue

                x = round(e.center[0] * self.screen_w)
                y = round(e.center[1] * self.screen_h)
                mid_x = self.screen_w // 2
                from_y = int(self.screen_h * 0.7)
                to_y = int(self.screen_h * 0.2)

                # base_macro is a full path (build_map stores full paths per screen)
                op_macro = list(base_macro)
                for _ in range(e.found_at_scroll):
                    op_macro.append({
                        "action": "swipe",
                        "x1": mid_x, "y1": from_y, "x2": mid_x, "y2": to_y,
                        "duration": 400, "wait": 0.5,
                    })
                op_macro.append({"action": "tap", "x": x, "y": y, "wait": 1.0})

                texts = prefix_texts + [e.text]
                op_id = _op_id(texts)
                if op_id in visited_ops:
                    continue
                visited_ops.add(op_id)

                op_type = "NAV" if e.leads_to else "ACT"
                desc = " → ".join(texts)
                ops[op_id] = Operation(
                    id=op_id, description=desc,
                    macro=op_macro, type=op_type,
                )

                if e.leads_to:
                    _explore(e.leads_to, texts, depth + 1)

        _explore("screen_0", [], 0)
        return ops

    def format_ops_catalog(self, ops: dict[str, Operation]) -> str:
        """Format operations catalog for LLM consumption.

        Includes aliases so the LLM can match "打开无线" → op_wifi_on
        even when the op_id doesn't contain the exact term.
        """
        lines = []
        for op_id, op in ops.items():
            tag = "[ACT]" if op.type == "ACT" else "[NAV]"
            line = f"  {tag} {op_id} — {op.description}"
            # Collect aliases from the last element in the macro path
            last_text = op.description.split(" → ")[-1] if " → " in op.description else op.description
            found_aliases = False
            for screen in self.screens:
                if found_aliases:
                    break
                for e in screen.elements:
                    if e.text == last_text and e.aliases:
                        line += f"  [aliases: {', '.join(e.aliases)}]"
                        found_aliases = True
                        break
            lines.append(line)
        return "\n".join(lines)

    def build_enriched_screen_hint(self, screen_id: str) -> str:
        """Build a rich VLM hint for a screen, including description and element types.

        Returns empty string if the screen is not found.
        """
        screen = self.get_screen(screen_id)
        if not screen:
            return ""

        parts = [f"You are on \"{screen_id}\""]
        if screen.description:
            parts[0] += f": {screen.description}"
        parts[0] += "."

        # Group nav targets by semantic type
        nav_targets = self.get_nav_targets(screen_id)
        if nav_targets:
            parts.append(f"Navigation targets: {', '.join(nav_targets)}")
        else:
            # No nav targets — list fixed elements as visual reference points
            screen = self.get_screen(screen_id)
            if screen:
                refs = [e.text for e in screen.elements if e.fixed and e.text]
                if refs:
                    parts.append(f"Reference elements: {', '.join(refs[:8])}")

        if screen.scrollable:
            direction = screen.scroll_direction or "vertical"
            parts.append(f"This screen is {direction}-scrollable.")

        return " ".join(parts)


