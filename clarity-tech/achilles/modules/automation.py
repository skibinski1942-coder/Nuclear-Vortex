"""
Automation Module
=================

Provides workflow automation, scheduled tasks, and
automated action sequences for Achilles.
"""

import logging
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import json

logger = logging.getLogger(__name__)


class TriggerType(Enum):
    """Types of automation triggers."""
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    EVENT = "event"
    CONDITION = "condition"


class ActionType(Enum):
    """Types of automation actions."""
    EXECUTE = "execute"
    NOTIFY = "notify"
    TRANSFORM = "transform"
    CONDITIONAL = "conditional"
    LOOP = "loop"
    PARALLEL = "parallel"


@dataclass
class AutomationAction:
    """A single automation action."""
    id: str
    action_type: ActionType
    name: str
    config: Dict[str, Any] = field(default_factory=dict)
    next_action: Optional[str] = None
    on_error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "action_type": self.action_type.value,
            "name": self.name,
            "config": self.config,
            "next_action": self.next_action,
            "on_error": self.on_error,
        }


@dataclass
class Workflow:
    """Represents an automation workflow."""
    id: str
    name: str
    description: str
    trigger_type: TriggerType
    trigger_config: Dict[str, Any] = field(default_factory=dict)
    actions: List[AutomationAction] = field(default_factory=list)
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    last_run: Optional[datetime] = None
    run_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "trigger_type": self.trigger_type.value,
            "trigger_config": self.trigger_config,
            "actions": [a.to_dict() for a in self.actions],
            "enabled": self.enabled,
            "created_at": self.created_at.isoformat(),
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "run_count": self.run_count,
        }


@dataclass 
class WorkflowRun:
    """Records a single workflow execution."""
    id: str
    workflow_id: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str = "running"
    results: List[Dict[str, Any]] = field(default_factory=list)
    error: Optional[str] = None


class AutomationModule:
    """
    Automation Module for Achilles.
    
    Features:
    - Workflow definition and management
    - Trigger-based automation
    - Action chaining and parallel execution
    - Conditional logic and loops
    - Error handling and recovery
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Automation Module.
        
        Args:
            config: Module configuration.
        """
        self.config = config or {}
        
        # Workflow storage
        self.workflows: Dict[str, Workflow] = {}
        self.workflow_runs: List[WorkflowRun] = []
        
        # Action handlers
        self.action_handlers: Dict[str, Callable] = {}
        self._register_default_handlers()
        
        # Event listeners
        self.event_listeners: Dict[str, List[str]] = {}
        
        # Scheduled tasks
        self.scheduled_tasks: Dict[str, asyncio.Task] = {}
        
        # Statistics
        self.stats = {
            "workflows_created": 0,
            "workflows_executed": 0,
            "actions_executed": 0,
            "errors": 0,
        }
        
        logger.info("Automation Module initialized")
    
    def _register_default_handlers(self) -> None:
        """Register default action handlers."""
        self.action_handlers = {
            "log": self._action_log,
            "delay": self._action_delay,
            "transform": self._action_transform,
            "condition": self._action_condition,
            "loop": self._action_loop,
            "http_request": self._action_http_request,
            "set_variable": self._action_set_variable,
            "get_variable": self._action_get_variable,
        }
    
    # =========================================================================
    # Workflow Management
    # =========================================================================
    
    def create_workflow(
        self,
        name: str,
        description: str,
        trigger_type: TriggerType = TriggerType.MANUAL,
        trigger_config: Optional[Dict[str, Any]] = None,
        actions: Optional[List[Dict[str, Any]]] = None
    ) -> Workflow:
        """
        Create a new automation workflow.
        
        Args:
            name: Workflow name.
            description: Workflow description.
            trigger_type: How the workflow is triggered.
            trigger_config: Configuration for the trigger.
            actions: List of action definitions.
            
        Returns:
            The created Workflow.
        """
        workflow_id = f"wf_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        # Convert action definitions to AutomationAction objects
        workflow_actions = []
        if actions:
            for i, action_def in enumerate(actions):
                action = AutomationAction(
                    id=f"{workflow_id}_action_{i}",
                    action_type=ActionType(action_def.get("type", "execute")),
                    name=action_def.get("name", f"Action {i}"),
                    config=action_def.get("config", {}),
                    next_action=action_def.get("next_action"),
                    on_error=action_def.get("on_error"),
                )
                workflow_actions.append(action)
        
        workflow = Workflow(
            id=workflow_id,
            name=name,
            description=description,
            trigger_type=trigger_type,
            trigger_config=trigger_config or {},
            actions=workflow_actions,
        )
        
        self.workflows[workflow_id] = workflow
        self.stats["workflows_created"] += 1
        
        # Set up trigger if scheduled
        if trigger_type == TriggerType.SCHEDULED:
            self._setup_schedule(workflow)
        elif trigger_type == TriggerType.EVENT:
            self._setup_event_listener(workflow)
        
        logger.info(f"Created workflow: {workflow_id} - {name}")
        return workflow
    
    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """Get a workflow by ID."""
        return self.workflows.get(workflow_id)
    
    def list_workflows(self, enabled_only: bool = False) -> List[Workflow]:
        """List all workflows."""
        workflows = list(self.workflows.values())
        if enabled_only:
            workflows = [w for w in workflows if w.enabled]
        return workflows
    
    def update_workflow(
        self,
        workflow_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Workflow]:
        """Update a workflow."""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return None
        
        for key, value in updates.items():
            if hasattr(workflow, key):
                setattr(workflow, key, value)
        
        return workflow
    
    def delete_workflow(self, workflow_id: str) -> bool:
        """Delete a workflow."""
        if workflow_id in self.workflows:
            # Cancel any scheduled tasks
            if workflow_id in self.scheduled_tasks:
                self.scheduled_tasks[workflow_id].cancel()
                del self.scheduled_tasks[workflow_id]
            
            del self.workflows[workflow_id]
            logger.info(f"Deleted workflow: {workflow_id}")
            return True
        return False
    
    # =========================================================================
    # Workflow Execution
    # =========================================================================
    
    async def execute_workflow(
        self,
        workflow_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> WorkflowRun:
        """
        Execute a workflow.
        
        Args:
            workflow_id: ID of the workflow to execute.
            context: Initial context/variables for execution.
            
        Returns:
            WorkflowRun with execution results.
        """
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")
        
        if not workflow.enabled:
            raise ValueError(f"Workflow is disabled: {workflow_id}")
        
        # Create run record
        run = WorkflowRun(
            id=f"run_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
            workflow_id=workflow_id,
            started_at=datetime.now(),
        )
        
        # Initialize execution context
        exec_context = {
            "workflow_id": workflow_id,
            "run_id": run.id,
            "variables": context or {},
            "results": [],
        }
        
        try:
            # Execute actions in sequence
            for action in workflow.actions:
                try:
                    result = await self._execute_action(action, exec_context)
                    run.results.append({
                        "action_id": action.id,
                        "success": True,
                        "result": result,
                    })
                    exec_context["results"].append(result)
                    self.stats["actions_executed"] += 1
                    
                except Exception as e:
                    run.results.append({
                        "action_id": action.id,
                        "success": False,
                        "error": str(e),
                    })
                    
                    # Handle error based on action config
                    if action.on_error:
                        # Execute error handler
                        pass
                    else:
                        raise
            
            run.status = "completed"
            run.completed_at = datetime.now()
            
        except Exception as e:
            run.status = "failed"
            run.error = str(e)
            run.completed_at = datetime.now()
            self.stats["errors"] += 1
            logger.error(f"Workflow {workflow_id} failed: {e}")
        
        # Update workflow stats
        workflow.last_run = run.started_at
        workflow.run_count += 1
        
        # Store run
        self.workflow_runs.append(run)
        self.stats["workflows_executed"] += 1
        
        return run
    
    async def _execute_action(
        self,
        action: AutomationAction,
        context: Dict[str, Any]
    ) -> Any:
        """Execute a single action."""
        handler_name = action.config.get("handler", action.name.lower())
        handler = self.action_handlers.get(handler_name)
        
        if handler:
            return await self._run_handler(handler, action, context)
        else:
            # Try to execute as a generic action
            return await self._generic_action(action, context)
    
    async def _run_handler(
        self,
        handler: Callable,
        action: AutomationAction,
        context: Dict[str, Any]
    ) -> Any:
        """Run an action handler."""
        if asyncio.iscoroutinefunction(handler):
            return await handler(action, context)
        else:
            return handler(action, context)
    
    async def _generic_action(
        self,
        action: AutomationAction,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generic action execution."""
        return {
            "action_id": action.id,
            "action_name": action.name,
            "status": "executed",
            "config": action.config,
        }
    
    # =========================================================================
    # Default Action Handlers
    # =========================================================================
    
    async def _action_log(
        self,
        action: AutomationAction,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Log a message."""
        message = action.config.get("message", "")
        level = action.config.get("level", "info")
        
        # Substitute variables
        for key, value in context.get("variables", {}).items():
            message = message.replace(f"{{{key}}}", str(value))
        
        getattr(logger, level)(f"[Workflow] {message}")
        
        return {"logged": message, "level": level}
    
    async def _action_delay(
        self,
        action: AutomationAction,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Wait for a specified duration."""
        seconds = action.config.get("seconds", 1)
        await asyncio.sleep(seconds)
        return {"delayed": seconds}
    
    async def _action_transform(
        self,
        action: AutomationAction,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Transform data."""
        input_var = action.config.get("input")
        transform = action.config.get("transform", "passthrough")
        output_var = action.config.get("output")
        
        value = context["variables"].get(input_var)
        
        if transform == "uppercase":
            result = str(value).upper()
        elif transform == "lowercase":
            result = str(value).lower()
        elif transform == "json_parse":
            result = json.loads(value)
        elif transform == "json_stringify":
            result = json.dumps(value)
        else:
            result = value
        
        if output_var:
            context["variables"][output_var] = result
        
        return {"transformed": result}
    
    async def _action_condition(
        self,
        action: AutomationAction,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Conditional execution."""
        condition = action.config.get("condition", "true")
        
        # Simple condition evaluation
        variables = context.get("variables", {})
        try:
            # Safe evaluation with limited scope
            result = eval(condition, {"__builtins__": {}}, variables)
        except Exception:
            result = False
        
        return {"condition": condition, "result": bool(result)}
    
    async def _action_loop(
        self,
        action: AutomationAction,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Loop execution."""
        iterations = action.config.get("iterations", 1)
        results = []
        
        for i in range(iterations):
            context["variables"]["_loop_index"] = i
            results.append({"iteration": i})
        
        return {"iterations": iterations, "results": results}
    
    async def _action_http_request(
        self,
        action: AutomationAction,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Make an HTTP request (placeholder)."""
        url = action.config.get("url")
        method = action.config.get("method", "GET")
        
        # In a real implementation, this would use aiohttp or similar
        return {
            "url": url,
            "method": method,
            "status": "simulated",
            "note": "HTTP requests require additional setup",
        }
    
    async def _action_set_variable(
        self,
        action: AutomationAction,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Set a variable in context."""
        name = action.config.get("name")
        value = action.config.get("value")
        
        context["variables"][name] = value
        return {"variable": name, "value": value}
    
    async def _action_get_variable(
        self,
        action: AutomationAction,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get a variable from context."""
        name = action.config.get("name")
        value = context["variables"].get(name)
        return {"variable": name, "value": value}
    
    # =========================================================================
    # Triggers
    # =========================================================================
    
    def _setup_schedule(self, workflow: Workflow) -> None:
        """Set up a scheduled workflow trigger."""
        interval = workflow.trigger_config.get("interval_seconds", 3600)
        
        async def schedule_loop():
            while workflow.enabled:
                await asyncio.sleep(interval)
                if workflow.enabled:
                    await self.execute_workflow(workflow.id)
        
        task = asyncio.create_task(schedule_loop())
        self.scheduled_tasks[workflow.id] = task
    
    def _setup_event_listener(self, workflow: Workflow) -> None:
        """Set up an event-based trigger."""
        event_name = workflow.trigger_config.get("event")
        if event_name:
            if event_name not in self.event_listeners:
                self.event_listeners[event_name] = []
            self.event_listeners[event_name].append(workflow.id)
    
    async def emit_event(
        self,
        event_name: str,
        data: Optional[Dict[str, Any]] = None
    ) -> List[WorkflowRun]:
        """
        Emit an event to trigger listening workflows.
        
        Args:
            event_name: Name of the event.
            data: Event data to pass to workflows.
            
        Returns:
            List of WorkflowRuns triggered.
        """
        runs = []
        workflow_ids = self.event_listeners.get(event_name, [])
        
        for wf_id in workflow_ids:
            try:
                run = await self.execute_workflow(wf_id, data)
                runs.append(run)
            except Exception as e:
                logger.error(f"Event trigger failed for {wf_id}: {e}")
        
        return runs
    
    # =========================================================================
    # Handler Registration
    # =========================================================================
    
    def register_action_handler(
        self,
        name: str,
        handler: Callable
    ) -> None:
        """
        Register a custom action handler.
        
        Args:
            name: Handler name.
            handler: The handler function.
        """
        self.action_handlers[name] = handler
        logger.info(f"Registered action handler: {name}")
    
    # =========================================================================
    # Status
    # =========================================================================
    
    def get_status(self) -> Dict[str, Any]:
        """Get automation module status."""
        return {
            "workflows_count": len(self.workflows),
            "active_workflows": len([w for w in self.workflows.values() if w.enabled]),
            "scheduled_tasks": len(self.scheduled_tasks),
            "event_listeners": {k: len(v) for k, v in self.event_listeners.items()},
            "registered_handlers": list(self.action_handlers.keys()),
            "stats": self.stats.copy(),
        }
