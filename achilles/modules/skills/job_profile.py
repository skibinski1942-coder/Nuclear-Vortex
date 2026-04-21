"""
Job Profile
===========

Defines the data structures and loader for mapping **job duties** to
Achilles skills.

Once you provide job duties, use ``JobProfileLoader.from_dict(...)`` to parse
them into a ``JobProfile`` and call ``SkillRegistry.apply_job_profile(profile)``
to restrict the agent to only the skills and actions that role requires.

Example job profile dict::

    {
        "title": "Customer Support Specialist",
        "department": "Support",
        "description": "Handle customer inquiries and process tickets.",
        "duties": [
            {
                "name": "Respond to customer emails",
                "description": "Read and reply to support emails within 4 hours.",
                "required_skills": ["communication", "document"],
                "actions": ["send_email", "read", "write"],
                "priority": "HIGH"
            },
            {
                "name": "Log support tickets",
                "description": "Create tickets in the CRM via its REST API.",
                "required_skills": ["web_api"],
                "actions": ["post", "get"],
                "priority": "MEDIUM"
            },
            {
                "name": "Generate weekly report",
                "description": "Pull ticket data and produce a Markdown summary.",
                "required_skills": ["web_api", "data_processing"],
                "actions": ["get", "paginate", "analyse", "generate_report"],
                "priority": "LOW"
            }
        ],
        "permissions": {
            "can_delete": false,
            "can_write_files": true,
            "api_write_enabled": true
        }
    }
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class DutyPriority(Enum):
    """Priority level for a job duty."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    BACKGROUND = "BACKGROUND"


@dataclass
class JobDuty:
    """
    A single job duty / responsibility.

    Attributes:
        name:            Short name for the duty.
        description:     Detailed description.
        required_skills: List of skill names needed (must exist in the registry).
        actions:         Specific actions within those skills that are permitted.
        priority:        Relative importance level.
        schedule:        Optional cron-style schedule string (e.g. ``"0 9 * * 1-5"``).
        metadata:        Arbitrary additional data.
    """
    name: str
    description: str
    required_skills: List[str]
    actions: List[str]
    priority: DutyPriority = DutyPriority.MEDIUM
    schedule: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "required_skills": self.required_skills,
            "actions": self.actions,
            "priority": self.priority.value,
            "schedule": self.schedule,
            "metadata": self.metadata,
        }


@dataclass
class JobPermissions:
    """
    Permission flags that govern what the agent is allowed to do in this role.

    Attributes:
        can_delete:          Allow destructive delete operations.
        can_write_files:     Allow writing to the local filesystem.
        api_write_enabled:   Allow POST/PUT/PATCH/DELETE HTTP methods.
        allowed_domains:     If non-empty, restrict API calls to these hostnames.
        max_emails_per_hour: Rate limit for outbound email.
    """
    can_delete: bool = False
    can_write_files: bool = True
    api_write_enabled: bool = True
    allowed_domains: List[str] = field(default_factory=list)
    max_emails_per_hour: int = 50

    def to_dict(self) -> Dict[str, Any]:
        return {
            "can_delete": self.can_delete,
            "can_write_files": self.can_write_files,
            "api_write_enabled": self.api_write_enabled,
            "allowed_domains": self.allowed_domains,
            "max_emails_per_hour": self.max_emails_per_hour,
        }


@dataclass
class JobProfile:
    """
    A complete job profile that describes an employee agent's role.

    Attributes:
        title:       Job title (e.g. ``"Customer Support Specialist"``).
        department:  Organisational department.
        description: Role summary.
        duties:      List of ``JobDuty`` objects.
        permissions: ``JobPermissions`` instance.
        created_at:  Profile creation timestamp.
        metadata:    Arbitrary additional data.
    """
    title: str
    department: str
    description: str
    duties: List[JobDuty]
    permissions: JobPermissions
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def get_required_skills(self) -> List[str]:
        """Return a deduplicated list of all skills needed by this profile."""
        skills: List[str] = []
        for duty in self.duties:
            for s in duty.required_skills:
                if s not in skills:
                    skills.append(s)
        return skills

    def get_permitted_actions(self) -> Dict[str, List[str]]:
        """Return ``{skill_name: [actions]}`` mapping for the whole profile."""
        permitted: Dict[str, List[str]] = {}
        for duty in self.duties:
            for skill_name in duty.required_skills:
                permitted.setdefault(skill_name, [])
                for action in duty.actions:
                    if action not in permitted[skill_name]:
                        permitted[skill_name].append(action)
        return permitted

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "department": self.department,
            "description": self.description,
            "duties": [d.to_dict() for d in self.duties],
            "permissions": self.permissions.to_dict(),
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }

    def summary(self) -> str:
        """Return a human-readable role summary."""
        duties_list = "\n".join(
            f"  • [{d.priority.value}] {d.name}: {d.description}" for d in self.duties
        )
        skills_list = ", ".join(self.get_required_skills()) or "(none)"
        return (
            f"Job Profile: {self.title} ({self.department})\n"
            f"Description: {self.description}\n\n"
            f"Duties ({len(self.duties)}):\n{duties_list}\n\n"
            f"Required Skills: {skills_list}\n"
        )


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------


class JobProfileLoader:
    """
    Parse and validate a job profile from a dict, JSON string, or file.

    Usage::

        # From a Python dict
        profile = JobProfileLoader.from_dict({...})

        # From a JSON string
        profile = JobProfileLoader.from_json('{"title": "...", ...}')

        # From a JSON file
        profile = JobProfileLoader.from_file("/path/to/profile.json")

        # Apply to a registry
        registry.apply_job_profile(profile)
    """

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> JobProfile:
        """
        Build a ``JobProfile`` from a plain dictionary.

        Args:
            data: Profile dict (see module docstring for schema).

        Returns:
            Validated ``JobProfile``.

        Raises:
            ValueError: If required fields are missing or invalid.
        """
        cls._validate(data)

        duties = [
            JobDuty(
                name=d["name"],
                description=d.get("description", ""),
                required_skills=d.get("required_skills", []),
                actions=d.get("actions", []),
                priority=DutyPriority(d.get("priority", "MEDIUM")),
                schedule=d.get("schedule"),
                metadata=d.get("metadata", {}),
            )
            for d in data.get("duties", [])
        ]

        perms_data = data.get("permissions", {})
        permissions = JobPermissions(
            can_delete=perms_data.get("can_delete", False),
            can_write_files=perms_data.get("can_write_files", True),
            api_write_enabled=perms_data.get("api_write_enabled", True),
            allowed_domains=perms_data.get("allowed_domains", []),
            max_emails_per_hour=perms_data.get("max_emails_per_hour", 50),
        )

        profile = JobProfile(
            title=data["title"],
            department=data.get("department", "General"),
            description=data.get("description", ""),
            duties=duties,
            permissions=permissions,
            metadata=data.get("metadata", {}),
        )

        logger.info(
            "Loaded job profile: %s (%d duties, %d skills)",
            profile.title,
            len(profile.duties),
            len(profile.get_required_skills()),
        )
        return profile

    @classmethod
    def from_json(cls, json_str: str) -> JobProfile:
        """Parse a JSON string into a ``JobProfile``."""
        data = json.loads(json_str)
        return cls.from_dict(data)

    @classmethod
    def from_file(cls, path: str) -> JobProfile:
        """Read a JSON file and return a ``JobProfile``."""
        p = Path(path)
        return cls.from_json(p.read_text(encoding="utf-8"))

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    @staticmethod
    def _validate(data: Dict[str, Any]) -> None:
        if "title" not in data or not data["title"]:
            raise ValueError("Job profile must have a non-empty 'title'.")
        for i, duty in enumerate(data.get("duties", [])):
            if "name" not in duty:
                raise ValueError(f"Duty at index {i} is missing 'name'.")
            if not isinstance(duty.get("required_skills", []), list):
                raise ValueError(
                    f"Duty '{duty['name']}': 'required_skills' must be a list."
                )
            if not isinstance(duty.get("actions", []), list):
                raise ValueError(
                    f"Duty '{duty['name']}': 'actions' must be a list."
                )
            priority_val = duty.get("priority", "MEDIUM")
            valid_priorities = {p.value for p in DutyPriority}
            if priority_val not in valid_priorities:
                raise ValueError(
                    f"Duty '{duty['name']}': invalid priority '{priority_val}'. "
                    f"Valid values: {valid_priorities}"
                )


__all__ = ["JobDuty", "JobPermissions", "JobProfile", "JobProfileLoader", "DutyPriority"]
