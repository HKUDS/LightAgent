"""iOS Agent for Android-Lab - iOS device automation support."""

from ios_agent.connection import IOSConnection
from ios_agent.executor import IOSExecutor
from ios_agent.actions import IOSActionHandler
from ios_agent.controller import IOSController

# These modules have heavy optional deps (cv2, zhipuai).
# Keep them lazy so core device modules are importable standalone.
try:
    from ios_agent.recorder import IOSRecorder
except ImportError:
    IOSRecorder = None  # type: ignore

try:
    from ios_agent.task import IOSTask
except ImportError:
    IOSTask = None  # type: ignore

__all__ = [
    'IOSConnection',
    'IOSExecutor',
    'IOSActionHandler',
    'IOSController',
    'IOSTask',
    'IOSRecorder',
]
