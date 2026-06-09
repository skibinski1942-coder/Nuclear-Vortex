"""
Achilles Modules
================

Extension modules providing specialized capabilities:
- Automation: Workflow and task automation
- Tasks: Digital task execution framework
- Integration: External service integrations
"""

from achilles.modules.automation import AutomationModule
from achilles.modules.digital_tasks import DigitalTaskExecutor

__all__ = [
    "AutomationModule",
    "DigitalTaskExecutor",
]
