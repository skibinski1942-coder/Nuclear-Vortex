"""
Achilles Modules
================

Extension modules providing specialized capabilities:
- Automation: Workflow and task automation
- Tasks: Digital task execution framework
- Skills: API-equipped employee skills framework
- Integration: External service integrations
"""

from achilles.modules.automation import AutomationModule
from achilles.modules.digital_tasks import DigitalTaskExecutor
from achilles.modules.skills import Skill, SkillRegistry

__all__ = [
    "AutomationModule",
    "DigitalTaskExecutor",
    "Skill",
    "SkillRegistry",
]
