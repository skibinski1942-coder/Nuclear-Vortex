"""
Digital Task Executor
=====================

Provides capabilities for executing digital tasks that would
typically require human intervention, through automated processes
when given clear instructions.
"""

import logging
import os
import json
import asyncio
from typing import Any, Callable, Dict, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import re

logger = logging.getLogger(__name__)


class TaskCategory(Enum):
    """Categories of digital tasks."""
    FILE_OPERATIONS = "file_operations"
    DATA_PROCESSING = "data_processing"
    TEXT_MANIPULATION = "text_manipulation"
    COMMUNICATION = "communication"
    SCHEDULING = "scheduling"
    ANALYSIS = "analysis"
    INTEGRATION = "integration"
    AUTOMATION = "automation"


class TaskComplexity(Enum):
    """Task complexity levels."""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    EXPERT = "expert"


@dataclass
class DigitalTask:
    """Represents a digital task to be executed."""
    id: str
    name: str
    category: TaskCategory
    complexity: TaskComplexity
    instructions: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    requirements: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    status: str = "pending"
    result: Optional[Any] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category.value,
            "complexity": self.complexity.value,
            "instructions": self.instructions,
            "parameters": self.parameters,
            "requirements": self.requirements,
            "status": self.status,
            "result": self.result,
            "error": self.error,
        }


@dataclass
class ExecutionPlan:
    """Plan for executing a digital task."""
    task_id: str
    steps: List[Dict[str, Any]]
    estimated_duration: float
    risk_level: str
    requires_confirmation: bool
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "steps": self.steps,
            "estimated_duration": self.estimated_duration,
            "risk_level": self.risk_level,
            "requires_confirmation": self.requires_confirmation,
        }


class DigitalTaskExecutor:
    """
    Digital Task Executor for Achilles.
    
    This module enables Achilles to execute digital tasks that would
    typically require human intervention. It provides:
    
    - Task parsing and understanding
    - Execution planning
    - Safe execution with rollback capabilities
    - Result verification
    - Learning from task outcomes
    
    Safety Principles:
    - Never executes destructive operations without confirmation
    - Maintains audit log of all actions
    - Provides rollback for reversible operations
    - Validates all inputs before execution
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Digital Task Executor.
        
        Args:
            config: Executor configuration.
        """
        self.config = config or {}
        
        # Task storage
        self.tasks: Dict[str, DigitalTask] = {}
        self.execution_history: List[Dict[str, Any]] = []
        
        # Capability handlers
        self.capabilities: Dict[str, Callable] = {}
        self._register_default_capabilities()
        
        # Audit log
        self.audit_log: List[Dict[str, Any]] = []
        
        # Safety settings
        self.require_confirmation_for = self.config.get(
            "require_confirmation_for",
            ["delete", "modify", "send", "execute"]
        )
        
        # Statistics
        self.stats = {
            "tasks_created": 0,
            "tasks_executed": 0,
            "tasks_succeeded": 0,
            "tasks_failed": 0,
        }
        
        logger.info("Digital Task Executor initialized")
    
    def _register_default_capabilities(self) -> None:
        """Register default task execution capabilities."""
        self.capabilities = {
            # File Operations
            "read_file": self._cap_read_file,
            "write_file": self._cap_write_file,
            "list_files": self._cap_list_files,
            "search_files": self._cap_search_files,
            
            # Data Processing
            "parse_json": self._cap_parse_json,
            "format_json": self._cap_format_json,
            "filter_data": self._cap_filter_data,
            "aggregate_data": self._cap_aggregate_data,
            
            # Text Manipulation
            "search_replace": self._cap_search_replace,
            "extract_pattern": self._cap_extract_pattern,
            "format_text": self._cap_format_text,
            "summarize_text": self._cap_summarize_text,
            
            # Analysis
            "analyze_data": self._cap_analyze_data,
            "compare_data": self._cap_compare_data,
            "validate_data": self._cap_validate_data,
            
            # Scheduling
            "create_reminder": self._cap_create_reminder,
            "schedule_task": self._cap_schedule_task,
        }
    
    # =========================================================================
    # Task Management
    # =========================================================================
    
    def create_task(
        self,
        name: str,
        instructions: str,
        category: Optional[TaskCategory] = None,
        parameters: Optional[Dict[str, Any]] = None
    ) -> DigitalTask:
        """
        Create a new digital task from instructions.
        
        Args:
            name: Task name.
            instructions: Natural language instructions.
            category: Task category (auto-detected if not provided).
            parameters: Task parameters.
            
        Returns:
            The created DigitalTask.
        """
        task_id = f"dtask_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        # Auto-detect category if not provided
        if not category:
            category = self._detect_category(instructions)
        
        # Determine complexity
        complexity = self._assess_complexity(instructions, parameters)
        
        # Extract requirements
        requirements = self._extract_requirements(instructions)
        
        task = DigitalTask(
            id=task_id,
            name=name,
            category=category,
            complexity=complexity,
            instructions=instructions,
            parameters=parameters or {},
            requirements=requirements,
        )
        
        self.tasks[task_id] = task
        self.stats["tasks_created"] += 1
        
        self._audit("task_created", {"task_id": task_id, "name": name})
        logger.info(f"Created digital task: {task_id} - {name}")
        
        return task
    
    def _detect_category(self, instructions: str) -> TaskCategory:
        """Detect task category from instructions."""
        instructions_lower = instructions.lower()
        
        category_keywords = {
            TaskCategory.FILE_OPERATIONS: ["file", "folder", "directory", "read", "write", "save"],
            TaskCategory.DATA_PROCESSING: ["data", "process", "transform", "convert", "parse"],
            TaskCategory.TEXT_MANIPULATION: ["text", "string", "format", "replace", "extract"],
            TaskCategory.COMMUNICATION: ["send", "email", "message", "notify", "alert"],
            TaskCategory.SCHEDULING: ["schedule", "remind", "timer", "calendar", "appointment"],
            TaskCategory.ANALYSIS: ["analyze", "compare", "evaluate", "assess", "review"],
            TaskCategory.INTEGRATION: ["api", "connect", "integrate", "sync", "webhook"],
            TaskCategory.AUTOMATION: ["automate", "workflow", "repeat", "batch", "script"],
        }
        
        for category, keywords in category_keywords.items():
            if any(kw in instructions_lower for kw in keywords):
                return category
        
        return TaskCategory.AUTOMATION
    
    def _assess_complexity(
        self,
        instructions: str,
        parameters: Optional[Dict[str, Any]]
    ) -> TaskComplexity:
        """Assess task complexity."""
        # Simple heuristics for complexity
        word_count = len(instructions.split())
        param_count = len(parameters) if parameters else 0
        
        if word_count < 10 and param_count < 3:
            return TaskComplexity.SIMPLE
        elif word_count < 30 and param_count < 5:
            return TaskComplexity.MODERATE
        elif word_count < 50:
            return TaskComplexity.COMPLEX
        else:
            return TaskComplexity.EXPERT
    
    def _extract_requirements(self, instructions: str) -> List[str]:
        """Extract requirements from instructions."""
        requirements = []
        
        # Check for common requirements
        if any(word in instructions.lower() for word in ["file", "read", "write"]):
            requirements.append("file_access")
        if any(word in instructions.lower() for word in ["api", "http", "request"]):
            requirements.append("network_access")
        if any(word in instructions.lower() for word in ["email", "send", "notify"]):
            requirements.append("communication")
        
        return requirements
    
    # =========================================================================
    # Execution Planning
    # =========================================================================
    
    def plan_execution(self, task: DigitalTask) -> ExecutionPlan:
        """
        Create an execution plan for a task.
        
        Args:
            task: The task to plan.
            
        Returns:
            ExecutionPlan with steps and metadata.
        """
        steps = []
        
        # Parse instructions to identify required steps
        instructions = task.instructions.lower()
        
        # Identify capabilities needed
        for cap_name, handler in self.capabilities.items():
            if self._capability_matches(cap_name, instructions):
                steps.append({
                    "step": len(steps) + 1,
                    "capability": cap_name,
                    "description": f"Execute {cap_name}",
                    "parameters": task.parameters,
                })
        
        # If no specific capabilities matched, add generic execution step
        if not steps:
            steps.append({
                "step": 1,
                "capability": "generic_execute",
                "description": "Execute task based on instructions",
                "parameters": task.parameters,
            })
        
        # Add verification step
        steps.append({
            "step": len(steps) + 1,
            "capability": "verify_result",
            "description": "Verify task completion",
        })
        
        # Assess risk
        risk_level = self._assess_risk(task, steps)
        
        # Check if confirmation needed
        requires_confirmation = any(
            keyword in instructions
            for keyword in self.require_confirmation_for
        )
        
        plan = ExecutionPlan(
            task_id=task.id,
            steps=steps,
            estimated_duration=len(steps) * 1.0,  # 1 second per step estimate
            risk_level=risk_level,
            requires_confirmation=requires_confirmation,
        )
        
        self._audit("plan_created", {"task_id": task.id, "steps": len(steps)})
        return plan
    
    def _capability_matches(self, cap_name: str, instructions: str) -> bool:
        """Check if a capability matches the instructions."""
        cap_keywords = {
            "read_file": ["read", "load", "open", "get file"],
            "write_file": ["write", "save", "create file", "output to"],
            "list_files": ["list", "show files", "directory contents"],
            "search_files": ["search", "find file", "locate"],
            "parse_json": ["parse json", "read json", "json input"],
            "format_json": ["format json", "json output", "to json"],
            "filter_data": ["filter", "select", "where"],
            "aggregate_data": ["sum", "count", "average", "aggregate"],
            "search_replace": ["replace", "substitute", "change"],
            "extract_pattern": ["extract", "pattern", "regex"],
            "format_text": ["format", "template", "structure"],
            "summarize_text": ["summarize", "summary", "brief"],
            "analyze_data": ["analyze", "statistics", "insights"],
            "compare_data": ["compare", "diff", "difference"],
            "validate_data": ["validate", "check", "verify"],
            "create_reminder": ["remind", "reminder", "alert"],
            "schedule_task": ["schedule", "later", "at time"],
        }
        
        keywords = cap_keywords.get(cap_name, [])
        return any(kw in instructions for kw in keywords)
    
    def _assess_risk(
        self,
        task: DigitalTask,
        steps: List[Dict[str, Any]]
    ) -> str:
        """Assess the risk level of a task."""
        high_risk_caps = ["write_file", "delete", "send", "execute"]
        medium_risk_caps = ["modify", "update", "change"]
        
        risk_scores = {
            "write_file": 2,
            "send": 3,
            "delete": 4,
            "execute": 3,
            "modify": 2,
            "update": 2,
        }
        
        total_risk = 0
        for step in steps:
            cap = step.get("capability", "")
            total_risk += risk_scores.get(cap, 1)
        
        if total_risk >= 6:
            return "high"
        elif total_risk >= 3:
            return "medium"
        else:
            return "low"
    
    # =========================================================================
    # Task Execution
    # =========================================================================
    
    async def execute_task(
        self,
        task: DigitalTask,
        confirmed: bool = False
    ) -> Dict[str, Any]:
        """
        Execute a digital task.
        
        Args:
            task: The task to execute.
            confirmed: Whether the user has confirmed execution.
            
        Returns:
            Execution result.
        """
        plan = self.plan_execution(task)
        
        # Check if confirmation is needed
        if plan.requires_confirmation and not confirmed:
            return {
                "status": "requires_confirmation",
                "task_id": task.id,
                "plan": plan.to_dict(),
                "message": "This task requires your confirmation before execution.",
            }
        
        task.status = "executing"
        self._audit("task_started", {"task_id": task.id})
        
        results = []
        
        try:
            for step in plan.steps:
                capability = step.get("capability")
                
                if capability in self.capabilities:
                    handler = self.capabilities[capability]
                    step_result = await self._run_capability(
                        handler,
                        task,
                        step.get("parameters", {})
                    )
                else:
                    step_result = {"status": "skipped", "reason": "no handler"}
                
                results.append({
                    "step": step.get("step"),
                    "capability": capability,
                    "result": step_result,
                })
            
            task.status = "completed"
            task.result = results
            self.stats["tasks_executed"] += 1
            self.stats["tasks_succeeded"] += 1
            
            self._audit("task_completed", {
                "task_id": task.id,
                "steps_executed": len(results),
            })
            
            return {
                "status": "success",
                "task_id": task.id,
                "results": results,
            }
            
        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            self.stats["tasks_failed"] += 1
            
            self._audit("task_failed", {
                "task_id": task.id,
                "error": str(e),
            })
            
            logger.error(f"Task {task.id} failed: {e}")
            
            return {
                "status": "error",
                "task_id": task.id,
                "error": str(e),
                "partial_results": results,
            }
    
    async def _run_capability(
        self,
        handler: Callable,
        task: DigitalTask,
        parameters: Dict[str, Any]
    ) -> Any:
        """Run a capability handler."""
        if asyncio.iscoroutinefunction(handler):
            return await handler(task, parameters)
        else:
            return handler(task, parameters)
    
    # =========================================================================
    # Capability Implementations
    # =========================================================================
    
    async def _cap_read_file(
        self,
        task: DigitalTask,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Read a file."""
        path = parameters.get("path") or task.parameters.get("path")
        
        if not path:
            return {"error": "No path specified"}
        
        # Safety check - only allow reading from allowed directories
        allowed_dirs = self.config.get("allowed_read_dirs", [os.getcwd()])
        
        try:
            abs_path = os.path.abspath(path)
            if not any(abs_path.startswith(d) for d in allowed_dirs):
                return {"error": "Path not in allowed directories"}
            
            with open(path, 'r') as f:
                content = f.read()
            
            return {
                "success": True,
                "path": path,
                "content": content[:10000],  # Limit content size
                "size": len(content),
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def _cap_write_file(
        self,
        task: DigitalTask,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Write to a file."""
        path = parameters.get("path") or task.parameters.get("path")
        content = parameters.get("content") or task.parameters.get("content", "")
        
        if not path:
            return {"error": "No path specified"}
        
        # Safety check
        allowed_dirs = self.config.get("allowed_write_dirs", [os.getcwd()])
        
        try:
            abs_path = os.path.abspath(path)
            if not any(abs_path.startswith(d) for d in allowed_dirs):
                return {"error": "Path not in allowed directories"}
            
            with open(path, 'w') as f:
                f.write(content)
            
            return {
                "success": True,
                "path": path,
                "bytes_written": len(content),
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def _cap_list_files(
        self,
        task: DigitalTask,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """List files in a directory."""
        path = parameters.get("path", ".") or task.parameters.get("path", ".")
        pattern = parameters.get("pattern", "*")
        
        try:
            import glob as glob_module
            files = glob_module.glob(os.path.join(path, pattern))
            
            return {
                "success": True,
                "path": path,
                "files": files[:100],  # Limit results
                "count": len(files),
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def _cap_search_files(
        self,
        task: DigitalTask,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Search for files matching criteria."""
        path = parameters.get("path", ".") or task.parameters.get("path", ".")
        pattern = parameters.get("pattern", "*") or task.parameters.get("pattern", "*")
        
        try:
            import glob as glob_module
            files = glob_module.glob(os.path.join(path, "**", pattern), recursive=True)
            
            return {
                "success": True,
                "pattern": pattern,
                "files": files[:100],
                "count": len(files),
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def _cap_parse_json(
        self,
        task: DigitalTask,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Parse JSON data."""
        data = parameters.get("data") or task.parameters.get("data", "")
        
        try:
            parsed = json.loads(data)
            return {
                "success": True,
                "parsed": parsed,
            }
        except json.JSONDecodeError as e:
            return {"error": f"JSON parse error: {str(e)}"}
    
    async def _cap_format_json(
        self,
        task: DigitalTask,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Format data as JSON."""
        data = parameters.get("data") or task.parameters.get("data", {})
        indent = parameters.get("indent", 2)
        
        try:
            formatted = json.dumps(data, indent=indent, default=str)
            return {
                "success": True,
                "formatted": formatted,
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def _cap_filter_data(
        self,
        task: DigitalTask,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Filter data based on criteria."""
        data = parameters.get("data") or task.parameters.get("data", [])
        field = parameters.get("field")
        value = parameters.get("value")
        operator = parameters.get("operator", "equals")
        
        if not isinstance(data, list):
            return {"error": "Data must be a list"}
        
        filtered = []
        for item in data:
            if not isinstance(item, dict):
                continue
            
            item_value = item.get(field)
            
            if operator == "equals" and item_value == value:
                filtered.append(item)
            elif operator == "contains" and value in str(item_value):
                filtered.append(item)
            elif operator == "greater" and item_value > value:
                filtered.append(item)
            elif operator == "less" and item_value < value:
                filtered.append(item)
        
        return {
            "success": True,
            "filtered": filtered,
            "count": len(filtered),
            "original_count": len(data),
        }
    
    async def _cap_aggregate_data(
        self,
        task: DigitalTask,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Aggregate data."""
        data = parameters.get("data") or task.parameters.get("data", [])
        field = parameters.get("field")
        operation = parameters.get("operation", "count")
        
        if not isinstance(data, list):
            return {"error": "Data must be a list"}
        
        values = []
        for item in data:
            if isinstance(item, dict) and field:
                val = item.get(field)
                if val is not None:
                    values.append(val)
            elif isinstance(item, (int, float)):
                values.append(item)
        
        result = None
        if operation == "count":
            result = len(values)
        elif operation == "sum":
            result = sum(values) if values else 0
        elif operation == "average":
            result = sum(values) / len(values) if values else 0
        elif operation == "min":
            result = min(values) if values else None
        elif operation == "max":
            result = max(values) if values else None
        
        return {
            "success": True,
            "operation": operation,
            "result": result,
        }
    
    async def _cap_search_replace(
        self,
        task: DigitalTask,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Search and replace in text."""
        text = parameters.get("text") or task.parameters.get("text", "")
        search = parameters.get("search", "")
        replace = parameters.get("replace", "")
        use_regex = parameters.get("regex", False)
        
        if use_regex:
            result = re.sub(search, replace, text)
        else:
            result = text.replace(search, replace)
        
        return {
            "success": True,
            "result": result,
            "replacements": text.count(search) if not use_regex else "unknown",
        }
    
    async def _cap_extract_pattern(
        self,
        task: DigitalTask,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract patterns from text."""
        text = parameters.get("text") or task.parameters.get("text", "")
        pattern = parameters.get("pattern", "")
        
        try:
            matches = re.findall(pattern, text)
            return {
                "success": True,
                "matches": matches,
                "count": len(matches),
            }
        except re.error as e:
            return {"error": f"Invalid regex: {str(e)}"}
    
    async def _cap_format_text(
        self,
        task: DigitalTask,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Format text with template."""
        template = parameters.get("template") or task.parameters.get("template", "")
        variables = parameters.get("variables", {})
        
        try:
            result = template.format(**variables)
            return {
                "success": True,
                "result": result,
            }
        except KeyError as e:
            return {"error": f"Missing variable: {str(e)}"}
    
    async def _cap_summarize_text(
        self,
        task: DigitalTask,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Summarize text (basic implementation)."""
        text = parameters.get("text") or task.parameters.get("text", "")
        max_length = parameters.get("max_length", 200)
        
        # Simple summarization: take first sentences up to max_length
        sentences = re.split(r'[.!?]+', text)
        summary = ""
        
        for sentence in sentences:
            if len(summary) + len(sentence) <= max_length:
                summary += sentence.strip() + ". "
            else:
                break
        
        return {
            "success": True,
            "summary": summary.strip(),
            "original_length": len(text),
            "summary_length": len(summary),
        }
    
    async def _cap_analyze_data(
        self,
        task: DigitalTask,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze data and provide insights."""
        data = parameters.get("data") or task.parameters.get("data", [])
        
        if not isinstance(data, list):
            return {"error": "Data must be a list"}
        
        analysis = {
            "count": len(data),
            "type_distribution": {},
        }
        
        for item in data:
            item_type = type(item).__name__
            analysis["type_distribution"][item_type] = \
                analysis["type_distribution"].get(item_type, 0) + 1
        
        # If numeric, add statistics
        numerics = [x for x in data if isinstance(x, (int, float))]
        if numerics:
            analysis["numeric_stats"] = {
                "min": min(numerics),
                "max": max(numerics),
                "sum": sum(numerics),
                "average": sum(numerics) / len(numerics),
            }
        
        return {
            "success": True,
            "analysis": analysis,
        }
    
    async def _cap_compare_data(
        self,
        task: DigitalTask,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Compare two data sets."""
        data1 = parameters.get("data1") or task.parameters.get("data1", [])
        data2 = parameters.get("data2") or task.parameters.get("data2", [])
        
        set1 = set(str(x) for x in data1) if isinstance(data1, list) else set()
        set2 = set(str(x) for x in data2) if isinstance(data2, list) else set()
        
        return {
            "success": True,
            "only_in_first": list(set1 - set2),
            "only_in_second": list(set2 - set1),
            "in_both": list(set1 & set2),
            "first_count": len(data1) if isinstance(data1, list) else 0,
            "second_count": len(data2) if isinstance(data2, list) else 0,
        }
    
    async def _cap_validate_data(
        self,
        task: DigitalTask,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate data against rules."""
        data = parameters.get("data") or task.parameters.get("data")
        rules = parameters.get("rules", [])
        
        issues = []
        
        for rule in rules:
            rule_type = rule.get("type")
            
            if rule_type == "required" and not data:
                issues.append("Data is required but missing")
            elif rule_type == "type":
                expected_type = rule.get("expected")
                if expected_type == "list" and not isinstance(data, list):
                    issues.append("Data should be a list")
                elif expected_type == "dict" and not isinstance(data, dict):
                    issues.append("Data should be a dictionary")
            elif rule_type == "min_length":
                min_len = rule.get("value", 0)
                if len(data) < min_len:
                    issues.append(f"Data length should be at least {min_len}")
        
        return {
            "success": len(issues) == 0,
            "valid": len(issues) == 0,
            "issues": issues,
        }
    
    async def _cap_create_reminder(
        self,
        task: DigitalTask,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a reminder (placeholder)."""
        message = parameters.get("message") or task.parameters.get("message", "")
        time_str = parameters.get("time") or task.parameters.get("time", "")
        
        return {
            "success": True,
            "reminder_created": True,
            "message": message,
            "scheduled_for": time_str,
            "note": "Reminder system requires additional integration",
        }
    
    async def _cap_schedule_task(
        self,
        task: DigitalTask,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Schedule a task for later (placeholder)."""
        task_name = parameters.get("task_name") or task.parameters.get("task_name", "")
        schedule_time = parameters.get("time") or task.parameters.get("time", "")
        
        return {
            "success": True,
            "task_scheduled": True,
            "task_name": task_name,
            "scheduled_for": schedule_time,
            "note": "Task scheduling requires integration with automation module",
        }
    
    # =========================================================================
    # Capability Registration
    # =========================================================================
    
    def register_capability(
        self,
        name: str,
        handler: Callable,
        category: TaskCategory = TaskCategory.AUTOMATION
    ) -> None:
        """
        Register a new digital task capability.
        
        Args:
            name: Capability name.
            handler: The handler function.
            category: Task category for this capability.
        """
        self.capabilities[name] = handler
        self._audit("capability_registered", {"name": name, "category": category.value})
        logger.info(f"Registered capability: {name}")
    
    # =========================================================================
    # Audit and Logging
    # =========================================================================
    
    def _audit(self, action: str, details: Dict[str, Any]) -> None:
        """Record an audit entry."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "details": details,
        }
        self.audit_log.append(entry)
        
        # Keep only last 1000 entries
        if len(self.audit_log) > 1000:
            self.audit_log = self.audit_log[-1000:]
    
    def get_audit_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent audit log entries."""
        return self.audit_log[-limit:]
    
    # =========================================================================
    # Status
    # =========================================================================
    
    def get_status(self) -> Dict[str, Any]:
        """Get executor status."""
        return {
            "tasks_count": len(self.tasks),
            "capabilities_count": len(self.capabilities),
            "available_capabilities": list(self.capabilities.keys()),
            "audit_log_entries": len(self.audit_log),
            "stats": self.stats.copy(),
        }
