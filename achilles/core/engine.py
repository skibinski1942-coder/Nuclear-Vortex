"""
Achilles Core Engine
====================

The central processing engine that orchestrates all AI capabilities,
task management, and self-improvement systems.
"""

import json
import logging
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio

logger = logging.getLogger(__name__)


class Priority(Enum):
    """Task priority levels."""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    BACKGROUND = 5


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    WAITING_INPUT = "waiting_input"


@dataclass
class Task:
    """Represents a task to be executed by Achilles."""
    id: str
    name: str
    description: str
    priority: Priority = Priority.MEDIUM
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    dependencies: List[str] = field(default_factory=list)
    result: Optional[Any] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "priority": self.priority.name,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "dependencies": self.dependencies,
            "result": self.result,
            "error": self.error,
            "metadata": self.metadata,
        }


@dataclass
class PerformanceMetrics:
    """Tracks Achilles performance for self-improvement."""
    tasks_completed: int = 0
    tasks_failed: int = 0
    average_completion_time: float = 0.0
    success_rate: float = 1.0
    errors_mitigated: int = 0
    improvements_applied: int = 0
    knowledge_entries: int = 0
    
    def update_success_rate(self):
        """Recalculate success rate."""
        total = self.tasks_completed + self.tasks_failed
        if total > 0:
            self.success_rate = self.tasks_completed / total


class AchillesEngine:
    """
    The Core Engine of Achilles AI Assistant.
    
    This engine handles:
    - Task prioritization and execution
    - Self-monitoring and improvement
    - Knowledge management
    - Error detection and mitigation
    - Performance optimization
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Achilles Engine.
        
        Args:
            config: Configuration dictionary for engine settings.
        """
        self.config = config or {}
        self.tasks: Dict[str, Task] = {}
        self.task_queue: List[str] = []
        self.completed_tasks: List[str] = []
        self.knowledge_base: Dict[str, Any] = {}
        self.metrics = PerformanceMetrics()
        self.error_log: List[Dict[str, Any]] = []
        self.improvements: List[Dict[str, Any]] = []
        self.handlers: Dict[str, Callable] = {}
        self._running = False
        
        logger.info("Achilles Engine initialized")
    
    def register_handler(self, task_type: str, handler: Callable) -> None:
        """
        Register a handler function for a specific task type.
        
        Args:
            task_type: The type of task this handler processes.
            handler: The function to handle this task type.
        """
        self.handlers[task_type] = handler
        logger.info(f"Registered handler for task type: {task_type}")
    
    def create_task(
        self,
        name: str,
        description: str,
        priority: Priority = Priority.MEDIUM,
        dependencies: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Task:
        """
        Create a new task and add it to the queue.
        
        Args:
            name: Task name.
            description: Task description.
            priority: Task priority level.
            dependencies: List of task IDs this task depends on.
            metadata: Additional task metadata.
            
        Returns:
            The created Task object.
        """
        task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        task = Task(
            id=task_id,
            name=name,
            description=description,
            priority=priority,
            dependencies=dependencies or [],
            metadata=metadata or {},
        )
        
        self.tasks[task_id] = task
        self._insert_task_by_priority(task_id)
        
        logger.info(f"Created task: {task_id} - {name}")
        return task
    
    def _insert_task_by_priority(self, task_id: str) -> None:
        """Insert task into queue maintaining priority order."""
        task = self.tasks[task_id]
        
        # Find insertion point based on priority
        insert_idx = 0
        for idx, existing_id in enumerate(self.task_queue):
            existing_task = self.tasks[existing_id]
            if task.priority.value < existing_task.priority.value:
                insert_idx = idx
                break
            insert_idx = idx + 1
        
        self.task_queue.insert(insert_idx, task_id)
    
    def prioritize_tasks(self) -> List[Task]:
        """
        Re-prioritize and organize all pending tasks.
        
        Returns:
            List of tasks in priority order.
        """
        # Sort tasks by priority and dependencies
        pending_tasks = [
            self.tasks[tid] for tid in self.task_queue
            if self.tasks[tid].status == TaskStatus.PENDING
        ]
        
        # Sort by priority value (lower is higher priority)
        pending_tasks.sort(key=lambda t: (t.priority.value, t.created_at))
        
        # Update queue
        self.task_queue = [t.id for t in pending_tasks]
        
        logger.info(f"Prioritized {len(pending_tasks)} tasks")
        return pending_tasks
    
    def can_execute_task(self, task: Task) -> bool:
        """Check if task dependencies are satisfied."""
        for dep_id in task.dependencies:
            if dep_id in self.tasks:
                dep_task = self.tasks[dep_id]
                if dep_task.status != TaskStatus.COMPLETED:
                    return False
        return True
    
    async def execute_task(self, task: Task) -> Any:
        """
        Execute a single task.
        
        Args:
            task: The task to execute.
            
        Returns:
            The task result.
        """
        if not self.can_execute_task(task):
            task.status = TaskStatus.WAITING_INPUT
            logger.info(f"Task {task.id} waiting for dependencies")
            return None
        
        task.status = TaskStatus.IN_PROGRESS
        start_time = datetime.now()
        
        try:
            # Get handler for task type
            task_type = task.metadata.get("type", "default")
            handler = self.handlers.get(task_type)
            
            if handler:
                result = await self._run_handler(handler, task)
            else:
                # Default execution
                result = await self._default_execute(task)
            
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            task.result = result
            
            # Update metrics
            self.metrics.tasks_completed += 1
            completion_time = (task.completed_at - start_time).total_seconds()
            self._update_average_time(completion_time)
            
            # Move to completed
            if task.id in self.task_queue:
                self.task_queue.remove(task.id)
            self.completed_tasks.append(task.id)
            
            logger.info(f"Completed task: {task.id}")
            return result
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            self.metrics.tasks_failed += 1
            
            # Log error for analysis
            self._log_error(task, e)
            
            logger.error(f"Task {task.id} failed: {e}")
            raise
    
    async def _run_handler(self, handler: Callable, task: Task) -> Any:
        """Run a task handler, supporting both sync and async."""
        if asyncio.iscoroutinefunction(handler):
            return await handler(task)
        else:
            return handler(task)
    
    async def _default_execute(self, task: Task) -> Dict[str, Any]:
        """Default task execution when no specific handler exists."""
        return {
            "task_id": task.id,
            "status": "executed",
            "message": f"Task '{task.name}' processed with default handler",
            "timestamp": datetime.now().isoformat(),
        }
    
    def _update_average_time(self, new_time: float) -> None:
        """Update running average completion time."""
        total = self.metrics.tasks_completed
        if total == 1:
            self.metrics.average_completion_time = new_time
        else:
            avg = self.metrics.average_completion_time
            self.metrics.average_completion_time = (
                (avg * (total - 1) + new_time) / total
            )
    
    def _log_error(self, task: Task, error: Exception) -> None:
        """Log error for analysis and improvement."""
        error_entry = {
            "task_id": task.id,
            "task_name": task.name,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "timestamp": datetime.now().isoformat(),
            "task_metadata": task.metadata,
        }
        self.error_log.append(error_entry)
        self.metrics.update_success_rate()
    
    # =========================================================================
    # Self-Improvement System
    # =========================================================================
    
    def analyze_errors(self) -> List[Dict[str, Any]]:
        """
        Analyze error patterns to identify improvements.
        
        Returns:
            List of identified issues and suggested fixes.
        """
        if not self.error_log:
            return []
        
        analysis = []
        error_types: Dict[str, int] = {}
        
        # Count error types
        for error in self.error_log:
            etype = error["error_type"]
            error_types[etype] = error_types.get(etype, 0) + 1
        
        # Identify patterns
        for etype, count in error_types.items():
            if count >= 2:  # Pattern threshold
                analysis.append({
                    "pattern": f"Recurring {etype} errors",
                    "count": count,
                    "suggestion": f"Implement better handling for {etype}",
                    "priority": Priority.HIGH.name if count >= 5 else Priority.MEDIUM.name,
                })
        
        logger.info(f"Analyzed {len(self.error_log)} errors, found {len(analysis)} patterns")
        return analysis
    
    def apply_improvement(self, improvement: Dict[str, Any]) -> None:
        """
        Apply an improvement to the system.
        
        Args:
            improvement: Dictionary describing the improvement.
        """
        improvement["applied_at"] = datetime.now().isoformat()
        improvement["status"] = "applied"
        self.improvements.append(improvement)
        self.metrics.improvements_applied += 1
        
        logger.info(f"Applied improvement: {improvement.get('name', 'unnamed')}")
    
    def self_optimize(self) -> Dict[str, Any]:
        """
        Run self-optimization routine.
        
        Returns:
            Optimization report.
        """
        report = {
            "timestamp": datetime.now().isoformat(),
            "actions": [],
            "metrics_before": {
                "success_rate": self.metrics.success_rate,
                "avg_completion_time": self.metrics.average_completion_time,
            }
        }
        
        # Analyze and address errors
        error_analysis = self.analyze_errors()
        for issue in error_analysis:
            report["actions"].append({
                "type": "error_mitigation",
                "issue": issue["pattern"],
                "action": issue["suggestion"],
            })
        
        # Optimize task queue
        self.prioritize_tasks()
        report["actions"].append({
            "type": "task_optimization",
            "action": "Re-prioritized task queue",
        })
        
        # Clean up completed tasks (keep last 100)
        if len(self.completed_tasks) > 100:
            old_tasks = self.completed_tasks[:-100]
            for tid in old_tasks:
                if tid in self.tasks:
                    del self.tasks[tid]
            self.completed_tasks = self.completed_tasks[-100:]
            report["actions"].append({
                "type": "memory_optimization",
                "action": f"Cleaned up {len(old_tasks)} old task records",
            })
        
        report["metrics_after"] = {
            "success_rate": self.metrics.success_rate,
            "avg_completion_time": self.metrics.average_completion_time,
        }
        
        logger.info("Self-optimization completed")
        return report
    
    # =========================================================================
    # Knowledge Management
    # =========================================================================
    
    def add_knowledge(self, key: str, value: Any, category: str = "general") -> None:
        """
        Add knowledge to the knowledge base.
        
        Args:
            key: Knowledge identifier.
            value: The knowledge content.
            category: Category for organization.
        """
        if category not in self.knowledge_base:
            self.knowledge_base[category] = {}
        
        self.knowledge_base[category][key] = {
            "value": value,
            "added_at": datetime.now().isoformat(),
            "accessed_count": 0,
        }
        self.metrics.knowledge_entries += 1
        
        logger.info(f"Added knowledge: {category}/{key}")
    
    def get_knowledge(self, key: str, category: str = "general") -> Optional[Any]:
        """
        Retrieve knowledge from the knowledge base.
        
        Args:
            key: Knowledge identifier.
            category: Category to search in.
            
        Returns:
            The knowledge value or None if not found.
        """
        if category in self.knowledge_base and key in self.knowledge_base[category]:
            entry = self.knowledge_base[category][key]
            entry["accessed_count"] += 1
            return entry["value"]
        return None
    
    def search_knowledge(self, query: str) -> List[Dict[str, Any]]:
        """
        Search the knowledge base.
        
        Args:
            query: Search query string.
            
        Returns:
            List of matching knowledge entries.
        """
        results = []
        query_lower = query.lower()
        
        for category, entries in self.knowledge_base.items():
            for key, entry in entries.items():
                if query_lower in key.lower() or query_lower in str(entry["value"]).lower():
                    results.append({
                        "category": category,
                        "key": key,
                        "value": entry["value"],
                    })
        
        return results
    
    # =========================================================================
    # Status and Reporting
    # =========================================================================
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current engine status.
        
        Returns:
            Status dictionary with metrics and queue info.
        """
        return {
            "running": self._running,
            "metrics": {
                "tasks_completed": self.metrics.tasks_completed,
                "tasks_failed": self.metrics.tasks_failed,
                "success_rate": round(self.metrics.success_rate * 100, 2),
                "avg_completion_time": round(self.metrics.average_completion_time, 3),
                "errors_mitigated": self.metrics.errors_mitigated,
                "improvements_applied": self.metrics.improvements_applied,
                "knowledge_entries": self.metrics.knowledge_entries,
            },
            "queue": {
                "pending": len(self.task_queue),
                "completed": len(self.completed_tasks),
                "total": len(self.tasks),
            },
            "errors_logged": len(self.error_log),
        }
    
    def export_state(self) -> Dict[str, Any]:
        """Export complete engine state for persistence."""
        return {
            "version": "1.0.0",
            "exported_at": datetime.now().isoformat(),
            "tasks": {tid: t.to_dict() for tid, t in self.tasks.items()},
            "task_queue": self.task_queue,
            "completed_tasks": self.completed_tasks,
            "knowledge_base": self.knowledge_base,
            "error_log": self.error_log,
            "improvements": self.improvements,
            "metrics": {
                "tasks_completed": self.metrics.tasks_completed,
                "tasks_failed": self.metrics.tasks_failed,
                "average_completion_time": self.metrics.average_completion_time,
                "success_rate": self.metrics.success_rate,
                "errors_mitigated": self.metrics.errors_mitigated,
                "improvements_applied": self.metrics.improvements_applied,
                "knowledge_entries": self.metrics.knowledge_entries,
            },
        }
    
    async def run(self) -> None:
        """Start the engine main loop."""
        self._running = True
        logger.info("Achilles Engine started")
        
        while self._running:
            # Process pending tasks
            if self.task_queue:
                task_id = self.task_queue[0]
                task = self.tasks[task_id]
                
                if task.status == TaskStatus.PENDING:
                    try:
                        await self.execute_task(task)
                    except Exception as e:
                        logger.error(f"Error executing task: {e}")
            
            # Small delay to prevent busy loop
            await asyncio.sleep(0.1)
    
    def stop(self) -> None:
        """Stop the engine."""
        self._running = False
        logger.info("Achilles Engine stopped")
