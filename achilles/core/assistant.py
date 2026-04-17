"""
Achilles Assistant
==================

The main conversational AI assistant interface that integrates
with various AI providers and manages user interactions.
"""

import json
import logging
from typing import Any, Dict, List, Optional, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio

from achilles.core.engine import AchillesEngine, Task, Priority, TaskStatus
from achilles.core.memory import MemorySystem
from achilles.core.reasoning import ReasoningEngine

logger = logging.getLogger(__name__)


class ConversationRole(Enum):
    """Roles in a conversation."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass
class Message:
    """Represents a conversation message."""
    role: ConversationRole
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "role": self.role.value,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class Conversation:
    """Represents a conversation session."""
    id: str
    messages: List[Message] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    context: Dict[str, Any] = field(default_factory=dict)
    
    def add_message(self, role: ConversationRole, content: str, **metadata) -> Message:
        """Add a message to the conversation."""
        message = Message(role=role, content=content, metadata=metadata)
        self.messages.append(message)
        return message
    
    def get_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get conversation history."""
        messages = self.messages[-limit:] if limit else self.messages
        return [m.to_dict() for m in messages]


class AIProvider:
    """
    Base class for AI provider integrations.
    
    Supports multiple AI backends (OpenAI, Anthropic, local models, etc.)
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize AI provider.
        
        Args:
            config: Provider configuration including API keys, model settings.
        """
        self.config = config
        self.model = config.get("model", "default")
        self.temperature = config.get("temperature", 0.7)
        self.max_tokens = config.get("max_tokens", 2048)
    
    async def generate(
        self,
        messages: List[Dict[str, Any]],
        **kwargs
    ) -> str:
        """
        Generate a response from the AI model.
        
        Args:
            messages: List of conversation messages.
            **kwargs: Additional generation parameters.
            
        Returns:
            Generated response text.
        """
        # This is a placeholder - actual implementations would call
        # specific AI APIs (OpenAI, Anthropic, etc.)
        raise NotImplementedError("Subclasses must implement generate()")
    
    async def generate_with_functions(
        self,
        messages: List[Dict[str, Any]],
        functions: List[Dict[str, Any]],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate a response with function calling capability.
        
        Args:
            messages: Conversation messages.
            functions: Available functions the AI can call.
            **kwargs: Additional parameters.
            
        Returns:
            Response including potential function calls.
        """
        raise NotImplementedError("Subclasses must implement generate_with_functions()")


class LocalAIProvider(AIProvider):
    """
    Local/offline AI provider for rule-based responses.
    
    Provides fallback functionality when external APIs are unavailable.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.responses = config.get("responses", {})
        self.default_response = config.get(
            "default_response",
            "I understand your request. Let me process that for you."
        )
    
    async def generate(
        self,
        messages: List[Dict[str, Any]],
        **kwargs
    ) -> str:
        """Generate response using local processing."""
        if not messages:
            return self.default_response
        
        last_message = messages[-1].get("content", "").lower()
        
        # Simple pattern matching for common queries
        for pattern, response in self.responses.items():
            if pattern.lower() in last_message:
                return response
        
        return self.default_response
    
    async def generate_with_functions(
        self,
        messages: List[Dict[str, Any]],
        functions: List[Dict[str, Any]],
        **kwargs
    ) -> Dict[str, Any]:
        """Local function calling implementation."""
        content = await self.generate(messages)
        return {
            "content": content,
            "function_call": None,
        }


class AchillesAssistant:
    """
    Achilles AI Assistant - The main interface for users.
    
    Capabilities:
    - Conversational AI with context retention
    - Task automation and management
    - Digital task execution
    - Self-improvement and learning
    - Multi-provider AI support
    """
    
    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        ai_provider: Optional[AIProvider] = None
    ):
        """
        Initialize Achilles Assistant.
        
        Args:
            config: Configuration dictionary.
            ai_provider: AI provider for generating responses.
        """
        self.config = config or {}
        self.engine = AchillesEngine(self.config.get("engine", {}))
        self.memory = MemorySystem(self.config.get("memory", {}))
        self.reasoning = ReasoningEngine(self.config.get("reasoning", {}))
        
        # AI Provider setup
        if ai_provider:
            self.ai_provider = ai_provider
        else:
            # Default to local provider
            self.ai_provider = LocalAIProvider({
                "responses": self._get_default_responses(),
            })
        
        # Conversation management
        self.conversations: Dict[str, Conversation] = {}
        self.active_conversation_id: Optional[str] = None
        
        # Available capabilities/tools
        self.capabilities: Dict[str, Callable] = {}
        self._register_default_capabilities()
        
        # System prompt
        self.system_prompt = self._build_system_prompt()
        
        logger.info("Achilles Assistant initialized")
    
    def _get_default_responses(self) -> Dict[str, str]:
        """Default response patterns for local AI."""
        return {
            "hello": "Hello! I'm Achilles, your AI assistant. How can I help you today?",
            "help": "I can help you with:\n- Task management and automation\n- Answering questions\n- Processing and analyzing data\n- Digital task execution\nJust tell me what you need!",
            "status": "All systems operational. I'm ready to assist you.",
            "capabilities": "My capabilities include task automation, knowledge management, self-improvement systems, and intelligent conversation.",
        }
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt for AI interactions."""
        return """You are Achilles, an advanced AI assistant with the following capabilities:

1. TASK MANAGEMENT: You can create, prioritize, and execute tasks automatically.
2. KNOWLEDGE MANAGEMENT: You learn and retain information to improve over time.
3. SELF-IMPROVEMENT: You analyze your performance and optimize your operations.
4. DIGITAL TASK EXECUTION: You can automate various digital tasks when given clear instructions.

Guidelines:
- Be helpful, accurate, and efficient
- Ask for clarification when instructions are ambiguous
- Explain your actions and reasoning when appropriate
- Prioritize user safety and data protection
- Continuously learn and improve from interactions

You have access to various tools and functions to accomplish tasks. Use them appropriately."""
    
    def _register_default_capabilities(self) -> None:
        """Register default assistant capabilities."""
        self.capabilities = {
            "create_task": self._cap_create_task,
            "list_tasks": self._cap_list_tasks,
            "execute_task": self._cap_execute_task,
            "get_status": self._cap_get_status,
            "add_knowledge": self._cap_add_knowledge,
            "search_knowledge": self._cap_search_knowledge,
            "optimize": self._cap_optimize,
        }
        
        # Register as task handlers
        for name, handler in self.capabilities.items():
            self.engine.register_handler(name, handler)
    
    # =========================================================================
    # Capability Implementations
    # =========================================================================
    
    async def _cap_create_task(
        self,
        name: str,
        description: str,
        priority: str = "MEDIUM",
        **kwargs
    ) -> Dict[str, Any]:
        """Create a new task."""
        priority_enum = getattr(Priority, priority.upper(), Priority.MEDIUM)
        task = self.engine.create_task(
            name=name,
            description=description,
            priority=priority_enum,
            metadata=kwargs,
        )
        return {
            "success": True,
            "task_id": task.id,
            "message": f"Created task: {name}",
        }
    
    async def _cap_list_tasks(self, status: Optional[str] = None) -> Dict[str, Any]:
        """List tasks with optional status filter."""
        tasks = []
        for task in self.engine.tasks.values():
            if status is None or task.status.value == status:
                tasks.append(task.to_dict())
        return {
            "success": True,
            "tasks": tasks,
            "count": len(tasks),
        }
    
    async def _cap_execute_task(self, task_id: str) -> Dict[str, Any]:
        """Execute a specific task."""
        if task_id not in self.engine.tasks:
            return {"success": False, "error": "Task not found"}
        
        task = self.engine.tasks[task_id]
        try:
            result = await self.engine.execute_task(task)
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _cap_get_status(self) -> Dict[str, Any]:
        """Get system status."""
        return {
            "success": True,
            "status": self.engine.get_status(),
            "memory_status": self.memory.get_status(),
        }
    
    async def _cap_add_knowledge(
        self,
        key: str,
        value: Any,
        category: str = "general"
    ) -> Dict[str, Any]:
        """Add knowledge to the system."""
        self.engine.add_knowledge(key, value, category)
        return {
            "success": True,
            "message": f"Added knowledge: {key}",
        }
    
    async def _cap_search_knowledge(self, query: str) -> Dict[str, Any]:
        """Search the knowledge base."""
        results = self.engine.search_knowledge(query)
        return {
            "success": True,
            "results": results,
            "count": len(results),
        }
    
    async def _cap_optimize(self) -> Dict[str, Any]:
        """Run self-optimization."""
        report = self.engine.self_optimize()
        return {
            "success": True,
            "optimization_report": report,
        }
    
    # =========================================================================
    # Conversation Management
    # =========================================================================
    
    def create_conversation(self, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a new conversation session.
        
        Args:
            context: Optional initial context for the conversation.
            
        Returns:
            The conversation ID.
        """
        conv_id = f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        conversation = Conversation(id=conv_id, context=context or {})
        
        # Add system message
        conversation.add_message(
            ConversationRole.SYSTEM,
            self.system_prompt
        )
        
        self.conversations[conv_id] = conversation
        self.active_conversation_id = conv_id
        
        logger.info(f"Created conversation: {conv_id}")
        return conv_id
    
    def get_conversation(self, conv_id: Optional[str] = None) -> Optional[Conversation]:
        """Get a conversation by ID or the active conversation."""
        cid = conv_id or self.active_conversation_id
        return self.conversations.get(cid)
    
    async def chat(
        self,
        message: str,
        conv_id: Optional[str] = None
    ) -> str:
        """
        Send a message and get a response.
        
        Args:
            message: User message.
            conv_id: Optional conversation ID.
            
        Returns:
            Assistant response.
        """
        # Get or create conversation
        cid = conv_id or self.active_conversation_id
        if not cid or cid not in self.conversations:
            cid = self.create_conversation()
        
        conversation = self.conversations[cid]
        
        # Add user message
        conversation.add_message(ConversationRole.USER, message)
        
        # Process through reasoning engine for intent detection
        intent = self.reasoning.analyze_intent(message)
        
        # Check if this is a capability request
        if intent.get("is_capability_request"):
            response = await self._handle_capability_request(intent, message)
        else:
            # Generate AI response
            history = conversation.get_history()
            response = await self.ai_provider.generate(history)
        
        # Add assistant message
        conversation.add_message(ConversationRole.ASSISTANT, response)
        
        # Learn from interaction
        self.memory.add_interaction(message, response, intent)
        
        return response
    
    async def _handle_capability_request(
        self,
        intent: Dict[str, Any],
        message: str
    ) -> str:
        """Handle a detected capability request."""
        capability = intent.get("capability")
        params = intent.get("parameters", {})
        
        if capability in self.capabilities:
            handler = self.capabilities[capability]
            try:
                result = await handler(**params)
                return self._format_capability_result(capability, result)
            except Exception as e:
                logger.error(f"Capability error: {e}")
                return f"I encountered an error while executing that request: {str(e)}"
        
        return f"I understood you want to {capability}, but I'm still learning how to do that effectively."
    
    def _format_capability_result(
        self,
        capability: str,
        result: Dict[str, Any]
    ) -> str:
        """Format capability result for user-friendly output."""
        if not result.get("success"):
            return f"Sorry, the operation failed: {result.get('error', 'Unknown error')}"
        
        # Format based on capability type
        if capability == "list_tasks":
            tasks = result.get("tasks", [])
            if not tasks:
                return "No tasks found."
            lines = ["Here are your tasks:"]
            for t in tasks[:10]:  # Limit display
                lines.append(f"- [{t['priority']}] {t['name']}: {t['status']}")
            return "\n".join(lines)
        
        elif capability == "get_status":
            status = result.get("status", {})
            metrics = status.get("metrics", {})
            return (
                f"System Status:\n"
                f"- Success Rate: {metrics.get('success_rate', 0)}%\n"
                f"- Tasks Completed: {metrics.get('tasks_completed', 0)}\n"
                f"- Knowledge Entries: {metrics.get('knowledge_entries', 0)}"
            )
        
        elif capability == "create_task":
            return f"Task created successfully. Task ID: {result.get('task_id')}"
        
        elif capability == "search_knowledge":
            results = result.get("results", [])
            if not results:
                return "No matching knowledge found."
            lines = ["Found the following knowledge:"]
            for r in results[:5]:
                lines.append(f"- {r['key']}: {r['value']}")
            return "\n".join(lines)
        
        elif capability == "optimize":
            report = result.get("optimization_report", {})
            actions = report.get("actions", [])
            return f"Optimization complete. Performed {len(actions)} optimization actions."
        
        # Default formatting
        return f"Operation completed successfully: {result.get('message', 'Done')}"
    
    # =========================================================================
    # Automation Features
    # =========================================================================
    
    async def automate_workflow(
        self,
        workflow: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Execute an automated workflow.
        
        Args:
            workflow: List of workflow steps with actions and parameters.
            
        Returns:
            Workflow execution results.
        """
        results = {
            "success": True,
            "steps_completed": 0,
            "steps_failed": 0,
            "step_results": [],
        }
        
        for i, step in enumerate(workflow):
            action = step.get("action")
            params = step.get("parameters", {})
            
            step_result = {
                "step": i + 1,
                "action": action,
                "success": False,
            }
            
            try:
                if action in self.capabilities:
                    handler = self.capabilities[action]
                    result = await handler(**params)
                    step_result["success"] = result.get("success", False)
                    step_result["result"] = result
                    
                    if step_result["success"]:
                        results["steps_completed"] += 1
                    else:
                        results["steps_failed"] += 1
                else:
                    step_result["error"] = f"Unknown action: {action}"
                    results["steps_failed"] += 1
                    
            except Exception as e:
                step_result["error"] = str(e)
                results["steps_failed"] += 1
            
            results["step_results"].append(step_result)
            
            # Stop on failure if configured
            if not step_result["success"] and step.get("stop_on_failure", True):
                results["success"] = False
                break
        
        return results
    
    # =========================================================================
    # Digital Task Execution
    # =========================================================================
    
    def register_digital_capability(
        self,
        name: str,
        handler: Callable,
        description: str
    ) -> None:
        """
        Register a new digital task capability.
        
        Args:
            name: Capability name.
            handler: The handler function.
            description: Description of what this capability does.
        """
        self.capabilities[name] = handler
        self.engine.register_handler(name, handler)
        self.engine.add_knowledge(
            f"capability_{name}",
            {"description": description, "handler": name},
            category="capabilities"
        )
        
        logger.info(f"Registered digital capability: {name}")
    
    # =========================================================================
    # State Management
    # =========================================================================
    
    def get_full_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        return {
            "assistant": {
                "active_conversation": self.active_conversation_id,
                "total_conversations": len(self.conversations),
                "registered_capabilities": list(self.capabilities.keys()),
            },
            "engine": self.engine.get_status(),
            "memory": self.memory.get_status(),
            "reasoning": self.reasoning.get_status(),
        }
    
    def export_state(self) -> Dict[str, Any]:
        """Export complete assistant state."""
        return {
            "version": "1.0.0",
            "exported_at": datetime.now().isoformat(),
            "engine_state": self.engine.export_state(),
            "memory_state": self.memory.export_state(),
            "conversations": {
                cid: {
                    "messages": conv.get_history(),
                    "context": conv.context,
                }
                for cid, conv in self.conversations.items()
            },
        }
    
    def import_state(self, state: Dict[str, Any]) -> None:
        """Import previously exported state."""
        # This would restore the assistant to a previous state
        logger.info("State import not fully implemented yet")
        pass
