"""
Achilles Skills Framework
=========================

A registry of reusable, API-equipped capabilities that can be composed into
employee-style job profiles.

Usage::

    from achilles.modules.skills import SkillRegistry, Skill

    registry = SkillRegistry()
    registry.register(CommunicationSkill())
    result = await registry.execute("communication", "send_notification",
                                    {"message": "Hello", "channel": "general"})

Once you define job duties (via JobProfile / JobProfileLoader), the registry
automatically exposes only the actions that role is permitted to use.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Base Skill contract
# ---------------------------------------------------------------------------


class Skill(ABC):
    """
    Abstract base class for all Achilles skills.

    Every concrete skill must declare:
    - ``name``         – unique identifier used in the registry
    - ``description``  – human-readable summary
    - ``actions``      – dict mapping action names to coroutine methods

    Subclasses may also declare ``api_config`` to hold endpoint URLs, auth
    tokens, or other provider-specific settings supplied at runtime.
    """

    #: Unique skill identifier (lower-snake-case).
    name: str = "base_skill"

    #: Short, human-readable description.
    description: str = "Base skill"

    def __init__(self, api_config: Optional[Dict[str, Any]] = None) -> None:
        self.api_config: Dict[str, Any] = api_config or {}
        self._actions: Dict[str, Callable] = self._build_action_map()
        logger.debug("Skill '%s' initialised", self.name)

    # ------------------------------------------------------------------
    # Subclass helpers
    # ------------------------------------------------------------------

    @abstractmethod
    def _build_action_map(self) -> Dict[str, Callable]:
        """Return a dict mapping action name → bound async method."""

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_capabilities(self) -> Dict[str, Any]:
        """Return a metadata dict describing available actions."""
        return {
            "skill": self.name,
            "description": self.description,
            "actions": list(self._actions.keys()),
        }

    async def execute(self, action: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """
        Dispatch *action* with *params*.

        Args:
            action: Name of the action to invoke.
            params: Keyword arguments forwarded to the action handler.

        Returns:
            Whatever the action handler returns.

        Raises:
            ValueError: If *action* is not registered.
        """
        if action not in self._actions:
            raise ValueError(
                f"Skill '{self.name}' has no action '{action}'. "
                f"Available: {list(self._actions.keys())}"
            )
        handler = self._actions[action]
        result = await handler(**(params or {}))
        logger.debug("Skill '%s' executed action '%s'", self.name, action)
        return result

    def configure(self, api_config: Dict[str, Any]) -> None:
        """Update the API configuration at runtime."""
        self.api_config.update(api_config)


# ---------------------------------------------------------------------------
# Skill Registry
# ---------------------------------------------------------------------------


class SkillRegistry:
    """
    Central registry that holds all available skills and enforces job-profile
    permissions at execution time.

    Typical lifecycle::

        registry = SkillRegistry()
        registry.register(CommunicationSkill())
        registry.register(WebAPISkill())

        # Optionally load a job profile to restrict / describe permitted actions
        from achilles.modules.skills.job_profile import JobProfileLoader
        profile = JobProfileLoader.from_dict({...})
        registry.apply_job_profile(profile)

        result = await registry.execute("communication", "send_email", {...})
    """

    def __init__(self) -> None:
        self._skills: Dict[str, Skill] = {}
        self._job_profile: Optional[Any] = None  # JobProfile, set later
        logger.info("SkillRegistry created")

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(self, skill: Skill) -> None:
        """Register a skill instance."""
        self._skills[skill.name] = skill
        logger.info("Registered skill: %s", skill.name)

    def unregister(self, skill_name: str) -> None:
        """Remove a skill from the registry."""
        self._skills.pop(skill_name, None)

    # ------------------------------------------------------------------
    # Lookup helpers
    # ------------------------------------------------------------------

    def get(self, skill_name: str) -> Skill:
        """Return the skill with *skill_name* or raise ``KeyError``."""
        if skill_name not in self._skills:
            raise KeyError(f"No skill named '{skill_name}' in registry")
        return self._skills[skill_name]

    def list_skills(self) -> List[Dict[str, Any]]:
        """Return capability metadata for every registered skill."""
        return [s.get_capabilities() for s in self._skills.values()]

    # ------------------------------------------------------------------
    # Job-profile integration
    # ------------------------------------------------------------------

    def apply_job_profile(self, profile: Any) -> None:
        """
        Attach a ``JobProfile`` so that execution can enforce duty-based
        permissions.

        Args:
            profile: A ``JobProfile`` object (from job_profile module).
        """
        self._job_profile = profile
        logger.info("Applied job profile: %s", getattr(profile, "title", str(profile)))

    def get_permitted_actions(self) -> Dict[str, List[str]]:
        """
        Return skill → [actions] mapping filtered by the current job profile.

        If no profile is loaded all registered actions are returned.
        """
        if self._job_profile is None:
            return {s.name: list(s._actions.keys()) for s in self._skills.values()}

        permitted: Dict[str, List[str]] = {}
        for duty in getattr(self._job_profile, "duties", []):
            for skill_name in duty.required_skills:
                if skill_name in self._skills:
                    skill = self._skills[skill_name]
                    permitted.setdefault(skill_name, [])
                    for action in duty.actions:
                        if action in skill._actions and action not in permitted[skill_name]:
                            permitted[skill_name].append(action)
        return permitted

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    async def execute(
        self,
        skill_name: str,
        action: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        Execute *action* on the named skill, respecting job-profile
        permissions when a profile is loaded.

        Args:
            skill_name: Registry key for the target skill.
            action:     Action to invoke.
            params:     Parameters forwarded to the action.

        Returns:
            The action result.

        Raises:
            KeyError:        Skill not found.
            PermissionError: Action not permitted by the current job profile.
        """
        skill = self.get(skill_name)

        if self._job_profile is not None:
            permitted = self.get_permitted_actions()
            if skill_name not in permitted or action not in permitted[skill_name]:
                raise PermissionError(
                    f"Action '{action}' on skill '{skill_name}' is not permitted "
                    f"by the current job profile '{self._job_profile.title}'."
                )

        return await skill.execute(action, params)

    # ------------------------------------------------------------------
    # Factory helper
    # ------------------------------------------------------------------

    @classmethod
    def with_all_skills(
        cls,
        api_config: Optional[Dict[str, Any]] = None,
    ) -> "SkillRegistry":
        """
        Convenience factory that creates a registry pre-loaded with **all**
        built-in skills.

        Args:
            api_config: Optional dict with nested configs keyed by skill name,
                        e.g. ``{"communication": {"smtp_host": "..."}, ...}``.

        Returns:
            A fully populated ``SkillRegistry``.
        """
        from achilles.modules.skills.communication import CommunicationSkill
        from achilles.modules.skills.data_processing import DataProcessingSkill
        from achilles.modules.skills.document import DocumentSkill
        from achilles.modules.skills.scheduling import SchedulingSkill
        from achilles.modules.skills.web_api import WebAPISkill

        cfg = api_config or {}
        registry = cls()
        for skill_cls in (
            CommunicationSkill,
            SchedulingSkill,
            DocumentSkill,
            WebAPISkill,
            DataProcessingSkill,
        ):
            skill_name = skill_cls.name  # type: ignore[attr-defined]
            registry.register(skill_cls(cfg.get(skill_name, {})))
        return registry


__all__ = ["Skill", "SkillRegistry"]
