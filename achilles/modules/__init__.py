"""
Achilles Modules
================

Extension modules providing specialized capabilities:
- Automation: Workflow and task automation
- Tasks: Digital task execution framework
- Integration: External service integrations
- XRPLIntegration: XRP Ledger WebSocket & JSON-RPC integration
"""

from achilles.modules.automation import AutomationModule
from achilles.modules.digital_tasks import DigitalTaskExecutor
from achilles.modules.xrpl_integration import XRPLIntegration

__all__ = [
    "AutomationModule",
    "DigitalTaskExecutor",
    "XRPLIntegration",
]
