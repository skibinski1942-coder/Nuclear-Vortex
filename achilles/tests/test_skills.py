"""
Test Skills Framework
=====================

Tests for the Achilles skills layer:
- SkillRegistry
- CommunicationSkill
- SchedulingSkill
- DocumentSkill
- WebAPISkill
- DataProcessingSkill
- JobProfile / JobProfileLoader
"""

import asyncio
import json
import os
import tempfile
from datetime import datetime

import pytest

from achilles.modules.skills import Skill, SkillRegistry
from achilles.modules.skills.communication import CommunicationSkill
from achilles.modules.skills.data_processing import DataProcessingSkill
from achilles.modules.skills.document import DocumentSkill
from achilles.modules.skills.job_profile import (
    DutyPriority,
    JobDuty,
    JobPermissions,
    JobProfile,
    JobProfileLoader,
)
from achilles.modules.skills.scheduling import SchedulingSkill
from achilles.modules.skills.web_api import WebAPISkill


# ---------------------------------------------------------------------------
# SkillRegistry
# ---------------------------------------------------------------------------


class TestSkillRegistry:
    def test_register_and_get(self):
        registry = SkillRegistry()
        skill = CommunicationSkill()
        registry.register(skill)
        assert registry.get("communication") is skill

    def test_get_missing_skill_raises(self):
        registry = SkillRegistry()
        with pytest.raises(KeyError):
            registry.get("nonexistent")

    def test_list_skills(self):
        registry = SkillRegistry.with_all_skills()
        skills = registry.list_skills()
        names = {s["skill"] for s in skills}
        assert {"communication", "scheduling", "document", "web_api", "data_processing"} <= names

    def test_unregister(self):
        registry = SkillRegistry()
        registry.register(CommunicationSkill())
        registry.unregister("communication")
        with pytest.raises(KeyError):
            registry.get("communication")

    @pytest.mark.asyncio
    async def test_execute_dispatches_to_skill(self):
        registry = SkillRegistry()
        registry.register(CommunicationSkill())
        result = await registry.execute(
            "communication", "send_notification",
            {"message": "hello", "channel": "default"},
        )
        assert result["action"] == "send_notification"
        assert result["status"] == "dry_run"  # no webhook configured

    @pytest.mark.asyncio
    async def test_permission_enforcement(self):
        registry = SkillRegistry()
        registry.register(CommunicationSkill())

        duty = JobDuty(
            name="Notify only",
            description="",
            required_skills=["communication"],
            actions=["send_notification"],
        )
        profile = JobProfile(
            title="Notifier",
            department="Ops",
            description="",
            duties=[duty],
            permissions=JobPermissions(),
        )
        registry.apply_job_profile(profile)

        # Permitted action should succeed
        result = await registry.execute(
            "communication", "send_notification", {"message": "ok"}
        )
        assert result["action"] == "send_notification"

        # Denied action should raise PermissionError
        with pytest.raises(PermissionError):
            await registry.execute(
                "communication", "send_email",
                {"to": "x@x.com", "subject": "s", "body": "b"},
            )

    def test_get_permitted_actions_no_profile(self):
        registry = SkillRegistry()
        registry.register(CommunicationSkill())
        permitted = registry.get_permitted_actions()
        assert "communication" in permitted
        assert "send_email" in permitted["communication"]


# ---------------------------------------------------------------------------
# CommunicationSkill
# ---------------------------------------------------------------------------


class TestCommunicationSkill:
    def test_get_capabilities(self):
        skill = CommunicationSkill()
        caps = skill.get_capabilities()
        assert caps["skill"] == "communication"
        assert set(caps["actions"]) == {"send_email", "send_message", "send_notification"}

    @pytest.mark.asyncio
    async def test_send_notification_dry_run(self):
        skill = CommunicationSkill()
        result = await skill.execute(
            "send_notification", {"message": "Test", "channel": "ops"}
        )
        assert result["status"] == "dry_run"
        assert result["action"] == "send_notification"

    @pytest.mark.asyncio
    async def test_send_email_dry_run(self):
        skill = CommunicationSkill()
        result = await skill.execute(
            "send_email",
            {"to": "agent@example.com", "subject": "Hello", "body": "World"},
        )
        assert result["status"] == "dry_run"

    @pytest.mark.asyncio
    async def test_send_message_dry_run(self):
        skill = CommunicationSkill()
        result = await skill.execute(
            "send_message", {"text": "Hi team", "platform": "slack"}
        )
        assert result["status"] == "dry_run"

    @pytest.mark.asyncio
    async def test_unknown_action_raises(self):
        skill = CommunicationSkill()
        with pytest.raises(ValueError, match="no action"):
            await skill.execute("fly_to_the_moon", {})


# ---------------------------------------------------------------------------
# SchedulingSkill
# ---------------------------------------------------------------------------


class TestSchedulingSkill:
    @pytest.mark.asyncio
    async def test_create_event_local(self):
        skill = SchedulingSkill()
        result = await skill.execute(
            "create_event",
            {
                "title": "Team Standup",
                "start": "2025-01-20T09:00:00",
                "end": "2025-01-20T09:30:00",
                "attendees": ["alice@example.com", "bob@example.com"],
            },
        )
        assert result["action"] == "create_event"
        assert result["event"]["title"] == "Team Standup"
        assert "id" in result["event"]

    @pytest.mark.asyncio
    async def test_list_events_local(self):
        skill = SchedulingSkill()
        await skill.execute(
            "create_event",
            {
                "title": "Listing Test Event",
                "start": "2025-02-01T10:00:00",
                "end": "2025-02-01T11:00:00",
            },
        )
        result = await skill.execute(
            "list_events",
            {"start_date": "2025-01-01T00:00:00", "end_date": "2025-12-31T23:59:59"},
        )
        assert result["action"] == "list_events"
        assert isinstance(result["events"], list)

    @pytest.mark.asyncio
    async def test_set_reminder(self):
        skill = SchedulingSkill()
        result = await skill.execute(
            "set_reminder",
            {"task": "Submit timesheet", "due_at": "2025-01-31T17:00:00"},
        )
        assert result["action"] == "set_reminder"
        assert result["reminder"]["task"] == "Submit timesheet"

    @pytest.mark.asyncio
    async def test_check_availability_local(self):
        skill = SchedulingSkill()
        result = await skill.execute(
            "check_availability",
            {
                "attendees": ["alice@example.com"],
                "duration_minutes": 30,
            },
        )
        assert result["action"] == "check_availability"
        assert "suggested_slot" in result
        assert "slot_start" in result["suggested_slot"]

    @pytest.mark.asyncio
    async def test_cancel_event_local(self):
        skill = SchedulingSkill()
        create_result = await skill.execute(
            "create_event",
            {
                "title": "Event to Cancel",
                "start": "2025-03-01T08:00:00",
                "end": "2025-03-01T09:00:00",
            },
        )
        event_id = create_result["event"]["id"]
        cancel_result = await skill.execute("cancel_event", {"event_id": event_id})
        assert cancel_result["action"] == "cancel_event"
        assert cancel_result["removed"] == 1


# ---------------------------------------------------------------------------
# DocumentSkill
# ---------------------------------------------------------------------------


class TestDocumentSkill:
    @pytest.mark.asyncio
    async def test_write_and_read(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            skill = DocumentSkill({"base_path": tmpdir})
            write_result = await skill.execute(
                "write", {"path": "test.txt", "content": "Hello, Achilles!"}
            )
            assert write_result["status"] == "written"

            read_result = await skill.execute("read", {"path": "test.txt"})
            assert read_result["content"] == "Hello, Achilles!"

    @pytest.mark.asyncio
    async def test_list_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            skill = DocumentSkill({"base_path": tmpdir})
            for name in ("a.txt", "b.txt", "c.md"):
                await skill.execute("write", {"path": name, "content": "x"})

            list_result = await skill.execute("list", {})
            paths = [f["path"] for f in list_result["files"]]
            assert any("a.txt" in p for p in paths)
            assert any("b.txt" in p for p in paths)

    @pytest.mark.asyncio
    async def test_search(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            skill = DocumentSkill({"base_path": tmpdir})
            await skill.execute("write", {"path": "doc1.txt", "content": "AI and machine learning"})
            await skill.execute("write", {"path": "doc2.txt", "content": "Cloud computing trends"})

            result = await skill.execute("search", {"query": "machine learning"})
            assert result["count"] >= 1
            assert any("doc1.txt" in r["path"] for r in result["results"])

    @pytest.mark.asyncio
    async def test_delete_requires_confirmation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            skill = DocumentSkill({"base_path": tmpdir})
            await skill.execute("write", {"path": "to_delete.txt", "content": "bye"})

            # Without confirmation
            result = await skill.execute(
                "delete", {"path": "to_delete.txt", "confirmed": False}
            )
            assert result["status"] == "requires_confirmation"

            # With confirmation
            result = await skill.execute(
                "delete", {"path": "to_delete.txt", "confirmed": True}
            )
            assert result["status"] == "deleted"

    @pytest.mark.asyncio
    async def test_summarise(self):
        skill = DocumentSkill()
        long_text = (
            "Artificial intelligence is transforming industry. "
            "Machine learning models are now deployed at scale. "
            "Natural language processing has advanced rapidly. "
            "Computer vision systems surpass human accuracy on many benchmarks. "
            "Reinforcement learning has solved complex games. "
        ) * 3
        result = await skill.execute(
            "summarise", {"content": long_text, "max_sentences": 3}
        )
        assert result["action"] == "summarise"
        assert len(result["summary"]) > 0


# ---------------------------------------------------------------------------
# WebAPISkill
# ---------------------------------------------------------------------------


class TestWebAPISkill:
    def test_get_capabilities(self):
        skill = WebAPISkill()
        caps = skill.get_capabilities()
        assert "get" in caps["actions"]
        assert "post" in caps["actions"]
        assert "graphql" in caps["actions"]

    @pytest.mark.asyncio
    async def test_delete_requires_confirmation(self):
        skill = WebAPISkill()
        result = await skill.execute(
            "delete",
            {"url": "https://example.com/resource/1", "confirmed": False},
        )
        assert result["status"] == "requires_confirmation"

    def test_bearer_header(self):
        skill = WebAPISkill({"auth_mode": "bearer", "token": "mytoken"})
        headers = skill._build_headers()
        assert headers["Authorization"] == "Bearer mytoken"

    def test_api_key_header(self):
        skill = WebAPISkill({
            "auth_mode": "api_key",
            "api_key": "ABCD1234",
            "api_key_header": "X-API-Key",
        })
        headers = skill._build_headers()
        assert headers["X-API-Key"] == "ABCD1234"

    def test_basic_auth_header(self):
        import base64
        skill = WebAPISkill({
            "auth_mode": "basic",
            "username": "user",
            "password": "pass",
        })
        headers = skill._build_headers()
        expected = base64.b64encode(b"user:pass").decode()
        assert headers["Authorization"] == f"Basic {expected}"

    def test_resolve_url_relative(self):
        skill = WebAPISkill({"base_url": "https://api.example.com"})
        assert skill._resolve_url("/users") == "https://api.example.com/users"

    def test_resolve_url_absolute(self):
        skill = WebAPISkill({"base_url": "https://api.example.com"})
        full = "https://other.com/path"
        assert skill._resolve_url(full) == full


# ---------------------------------------------------------------------------
# DataProcessingSkill
# ---------------------------------------------------------------------------


class TestDataProcessingSkill:
    @pytest.mark.asyncio
    async def test_parse_json(self):
        skill = DataProcessingSkill()
        data = json.dumps([{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}])
        result = await skill.execute("parse", {"data": data, "fmt": "json"})
        assert result["row_count"] == 2
        assert result["rows"][0]["name"] == "Alice"

    @pytest.mark.asyncio
    async def test_parse_csv(self):
        skill = DataProcessingSkill()
        csv_data = "name,age\nAlice,30\nBob,25"
        result = await skill.execute("parse", {"data": csv_data, "fmt": "csv"})
        assert result["row_count"] == 2

    @pytest.mark.asyncio
    async def test_parse_jsonl(self):
        skill = DataProcessingSkill()
        jsonl = '{"x": 1}\n{"x": 2}\n{"x": 3}'
        result = await skill.execute("parse", {"data": jsonl, "fmt": "jsonl"})
        assert result["row_count"] == 3

    @pytest.mark.asyncio
    async def test_analyse(self):
        skill = DataProcessingSkill()
        rows = [{"name": "Alice", "score": "90"}, {"name": "Bob", "score": "80"}]
        result = await skill.execute(
            "analyse", {"rows": rows, "numeric_columns": ["score"]}
        )
        stats = result["stats"]
        assert stats["row_count"] == 2
        assert "score" in stats["numeric"]
        assert stats["numeric"]["score"]["mean"] == 85.0

    @pytest.mark.asyncio
    async def test_transform_filter(self):
        skill = DataProcessingSkill()
        rows = [{"val": 5}, {"val": 10}, {"val": 15}]
        result = await skill.execute(
            "transform",
            {
                "rows": rows,
                "filters": [{"column": "val", "op": "gt", "value": 7}],
            },
        )
        assert result["row_count"] == 2
        assert all(r["val"] > 7 for r in result["rows"])

    @pytest.mark.asyncio
    async def test_transform_sort_and_limit(self):
        skill = DataProcessingSkill()
        rows = [{"n": 3}, {"n": 1}, {"n": 2}]
        result = await skill.execute(
            "transform",
            {"rows": rows, "sort_by": "n", "sort_desc": False, "limit": 2},
        )
        assert result["rows"][0]["n"] == 1
        assert result["row_count"] == 2

    @pytest.mark.asyncio
    async def test_generate_report_markdown(self):
        skill = DataProcessingSkill()
        rows = [{"product": "Widget", "sales": "120"}, {"product": "Gadget", "sales": "95"}]
        result = await skill.execute(
            "generate_report",
            {"rows": rows, "title": "Sales Summary", "fmt": "markdown"},
        )
        assert "# Sales Summary" in result["report"]
        assert result["format"] == "markdown"

    @pytest.mark.asyncio
    async def test_merge_inner(self):
        skill = DataProcessingSkill()
        left = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
        right = [{"id": 1, "dept": "Eng"}, {"id": 3, "dept": "HR"}]
        result = await skill.execute(
            "merge", {"left": left, "right": right, "on": "id", "how": "inner"}
        )
        assert result["row_count"] == 1
        assert result["rows"][0]["name"] == "Alice"
        assert result["rows"][0]["dept"] == "Eng"

    @pytest.mark.asyncio
    async def test_export_json(self):
        skill = DataProcessingSkill()
        rows = [{"a": 1}, {"a": 2}]
        result = await skill.execute("export", {"rows": rows, "fmt": "json"})
        assert result["format"] == "json"
        exported = json.loads(result["content"])
        assert len(exported) == 2

    @pytest.mark.asyncio
    async def test_export_csv(self):
        skill = DataProcessingSkill()
        rows = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
        result = await skill.execute("export", {"rows": rows, "fmt": "csv"})
        assert result["format"] == "csv"
        assert "a,b" in result["content"]


# ---------------------------------------------------------------------------
# JobProfile / JobProfileLoader
# ---------------------------------------------------------------------------


class TestJobProfile:
    SAMPLE_PROFILE = {
        "title": "Customer Support Specialist",
        "department": "Support",
        "description": "Handle customer inquiries.",
        "duties": [
            {
                "name": "Respond to emails",
                "description": "Reply within 4 hours.",
                "required_skills": ["communication"],
                "actions": ["send_email", "send_notification"],
                "priority": "HIGH",
            },
            {
                "name": "Log tickets",
                "description": "Create CRM tickets.",
                "required_skills": ["web_api"],
                "actions": ["post", "get"],
                "priority": "MEDIUM",
            },
        ],
        "permissions": {
            "can_delete": False,
            "can_write_files": True,
            "api_write_enabled": True,
        },
    }

    def test_from_dict(self):
        profile = JobProfileLoader.from_dict(self.SAMPLE_PROFILE)
        assert profile.title == "Customer Support Specialist"
        assert len(profile.duties) == 2
        assert profile.permissions.can_delete is False

    def test_from_json(self):
        profile = JobProfileLoader.from_json(json.dumps(self.SAMPLE_PROFILE))
        assert profile.department == "Support"

    def test_from_file(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(self.SAMPLE_PROFILE, f)
            tmp_path = f.name
        try:
            profile = JobProfileLoader.from_file(tmp_path)
            assert profile.title == "Customer Support Specialist"
        finally:
            os.unlink(tmp_path)

    def test_required_skills(self):
        profile = JobProfileLoader.from_dict(self.SAMPLE_PROFILE)
        skills = profile.get_required_skills()
        assert "communication" in skills
        assert "web_api" in skills

    def test_permitted_actions(self):
        profile = JobProfileLoader.from_dict(self.SAMPLE_PROFILE)
        permitted = profile.get_permitted_actions()
        assert "send_email" in permitted["communication"]
        assert "post" in permitted["web_api"]

    def test_summary_contains_title(self):
        profile = JobProfileLoader.from_dict(self.SAMPLE_PROFILE)
        summary = profile.summary()
        assert "Customer Support Specialist" in summary
        assert "communication" in summary

    def test_invalid_profile_missing_title(self):
        with pytest.raises(ValueError, match="title"):
            JobProfileLoader.from_dict({"duties": []})

    def test_invalid_duty_priority(self):
        bad = dict(self.SAMPLE_PROFILE)
        bad["duties"] = [
            {
                "name": "Bad duty",
                "required_skills": [],
                "actions": [],
                "priority": "ULTRA",
            }
        ]
        with pytest.raises(ValueError, match="priority"):
            JobProfileLoader.from_dict(bad)

    def test_to_dict_roundtrip(self):
        profile = JobProfileLoader.from_dict(self.SAMPLE_PROFILE)
        d = profile.to_dict()
        assert d["title"] == "Customer Support Specialist"
        assert len(d["duties"]) == 2

    @pytest.mark.asyncio
    async def test_registry_with_job_profile(self):
        """End-to-end: registry + profile enforces only permitted skill actions."""
        registry = SkillRegistry.with_all_skills()
        profile = JobProfileLoader.from_dict(self.SAMPLE_PROFILE)
        registry.apply_job_profile(profile)

        permitted = registry.get_permitted_actions()
        assert "send_email" in permitted.get("communication", [])
        assert "post" in permitted.get("web_api", [])

        # scheduling is NOT in this profile → should raise PermissionError
        with pytest.raises(PermissionError):
            await registry.execute(
                "scheduling", "create_event",
                {"title": "X", "start": "2025-01-01T09:00:00", "end": "2025-01-01T10:00:00"},
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
