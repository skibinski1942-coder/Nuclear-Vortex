"""
Achilles Reasoning Engine
=========================

Handles intent detection, decision making, planning,
and logical reasoning for the AI assistant.
"""

import re
import logging
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class IntentType(Enum):
    """Types of user intents."""
    QUESTION = "question"
    COMMAND = "command"
    REQUEST = "request"
    FEEDBACK = "feedback"
    CORRECTION = "correction"
    GREETING = "greeting"
    FAREWELL = "farewell"
    CONFIRMATION = "confirmation"
    DENIAL = "denial"
    UNKNOWN = "unknown"


@dataclass
class Intent:
    """Represents a detected intent."""
    type: IntentType
    confidence: float
    capability: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    entities: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type.value,
            "confidence": self.confidence,
            "capability": self.capability,
            "parameters": self.parameters,
            "entities": self.entities,
        }


@dataclass
class ReasoningStep:
    """A step in the reasoning process."""
    step_number: int
    action: str
    reasoning: str
    result: Optional[Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "step": self.step_number,
            "action": self.action,
            "reasoning": self.reasoning,
            "result": self.result,
        }


class ReasoningEngine:
    """
    The Reasoning Engine for Achilles.
    
    Capabilities:
    - Intent detection and classification
    - Entity extraction
    - Decision making
    - Planning and goal decomposition
    - Logical reasoning chains
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Reasoning Engine.
        
        Args:
            config: Configuration settings.
        """
        self.config = config or {}
        
        # Intent patterns
        self.intent_patterns = self._build_intent_patterns()
        
        # Capability patterns
        self.capability_patterns = self._build_capability_patterns()
        
        # Reasoning history
        self.reasoning_history: List[Dict[str, Any]] = []
        
        # Statistics
        self.stats = {
            "intents_detected": 0,
            "decisions_made": 0,
            "plans_created": 0,
        }
        
        logger.info("Reasoning Engine initialized")
    
    def _build_intent_patterns(self) -> Dict[IntentType, List[str]]:
        """Build patterns for intent detection."""
        return {
            IntentType.QUESTION: [
                r"\?$",
                r"^(what|who|where|when|why|how|which|is|are|do|does|can|could|would|will)",
                r"(tell me|explain|describe)",
            ],
            IntentType.COMMAND: [
                r"^(do|make|create|delete|remove|update|change|set|run|execute|start|stop)",
                r"^please (do|make|create)",
            ],
            IntentType.REQUEST: [
                r"^(i want|i need|i would like|can you|could you|please)",
                r"(help me|assist me)",
            ],
            IntentType.FEEDBACK: [
                r"(good job|well done|thanks|thank you|great|excellent|perfect)",
                r"(bad|wrong|incorrect|not right|doesn't work)",
            ],
            IntentType.CORRECTION: [
                r"^(no|wrong|incorrect|that's not|actually)",
                r"(i meant|i mean|what i wanted)",
            ],
            IntentType.GREETING: [
                r"^(hi|hello|hey|good morning|good afternoon|good evening|greetings)",
            ],
            IntentType.FAREWELL: [
                r"^(bye|goodbye|see you|farewell|take care)",
            ],
            IntentType.CONFIRMATION: [
                r"^(yes|yeah|yep|correct|right|exactly|sure|ok|okay|confirm)",
            ],
            IntentType.DENIAL: [
                r"^(no|nope|nah|wrong|incorrect|cancel|stop|don't)",
            ],
        }
    
    def _build_capability_patterns(self) -> Dict[str, List[str]]:
        """Build patterns for capability detection."""
        return {
            "create_task": [
                r"(create|add|new|make) (a )?(task|todo|item)",
                r"(remind me|remember) to",
            ],
            "list_tasks": [
                r"(list|show|display|get) (all )?(my )?(tasks|todos|items)",
                r"what (are my|do i have) (tasks|todos)",
            ],
            "execute_task": [
                r"(execute|run|do|perform) (task|the task)",
                r"complete (the )?(task|this)",
            ],
            "get_status": [
                r"(status|how are you|system status|report)",
                r"(what's|what is) (your|the) status",
            ],
            "add_knowledge": [
                r"(remember|learn|store|save) (that|this)",
                r"(add|store) (to )?(knowledge|memory)",
            ],
            "search_knowledge": [
                r"(search|find|look up|query) (in )?(knowledge|memory)",
                r"(do you know|what do you know) about",
            ],
            "optimize": [
                r"(optimize|improve|enhance) (yourself|system|performance)",
                r"(self[- ]?improve|self[- ]?optimize)",
            ],
        }
    
    # =========================================================================
    # Intent Detection
    # =========================================================================
    
    def analyze_intent(self, text: str) -> Dict[str, Any]:
        """
        Analyze text to detect user intent.
        
        Args:
            text: The user input text.
            
        Returns:
            Dictionary with intent information.
        """
        text_lower = text.lower().strip()
        
        # Detect intent type
        intent_type = self._detect_intent_type(text_lower)
        
        # Detect capability
        capability, cap_confidence = self._detect_capability(text_lower)
        
        # Extract entities
        entities = self._extract_entities(text)
        
        # Extract parameters based on capability
        parameters = self._extract_parameters(text, capability)
        
        # Calculate overall confidence
        confidence = self._calculate_confidence(intent_type, capability, cap_confidence)
        
        intent = Intent(
            type=intent_type,
            confidence=confidence,
            capability=capability,
            parameters=parameters,
            entities=entities,
        )
        
        self.stats["intents_detected"] += 1
        
        result = intent.to_dict()
        result["is_capability_request"] = capability is not None
        result["is_feedback"] = intent_type == IntentType.FEEDBACK
        result["is_correction"] = intent_type == IntentType.CORRECTION
        
        return result
    
    def _detect_intent_type(self, text: str) -> IntentType:
        """Detect the type of intent."""
        for intent_type, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return intent_type
        return IntentType.UNKNOWN
    
    def _detect_capability(self, text: str) -> Tuple[Optional[str], float]:
        """Detect which capability is being requested."""
        for capability, patterns in self.capability_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    # Simple confidence based on pattern specificity
                    confidence = 0.8 if len(pattern) > 20 else 0.6
                    return capability, confidence
        return None, 0.0
    
    def _extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract entities from text."""
        entities = []
        
        # Extract quoted strings
        quotes = re.findall(r'"([^"]+)"', text)
        for q in quotes:
            entities.append({"type": "quoted_string", "value": q})
        
        # Extract numbers
        numbers = re.findall(r'\b(\d+)\b', text)
        for n in numbers:
            entities.append({"type": "number", "value": int(n)})
        
        # Extract dates (simple pattern)
        dates = re.findall(r'\b(\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{2,4})\b', text)
        for d in dates:
            entities.append({"type": "date", "value": d})
        
        # Extract priorities
        priorities = re.findall(r'\b(high|medium|low|critical|urgent)\b', text, re.IGNORECASE)
        for p in priorities:
            entities.append({"type": "priority", "value": p.upper()})
        
        return entities
    
    def _extract_parameters(self, text: str, capability: Optional[str]) -> Dict[str, Any]:
        """Extract parameters based on detected capability."""
        params = {}
        
        if not capability:
            return params
        
        if capability == "create_task":
            # Try to extract task name from quoted string
            quotes = re.findall(r'"([^"]+)"', text)
            if quotes:
                params["name"] = quotes[0]
                params["description"] = quotes[0]
            else:
                # Try to extract from natural language
                match = re.search(
                    r'(?:create|add|make) (?:a )?(?:task|todo)(?: (?:called|named|to))? (.+)',
                    text,
                    re.IGNORECASE
                )
                if match:
                    params["name"] = match.group(1).strip()
                    params["description"] = match.group(1).strip()
            
            # Extract priority
            priority_match = re.search(r'\b(high|medium|low|critical)\b', text, re.IGNORECASE)
            if priority_match:
                params["priority"] = priority_match.group(1).upper()
        
        elif capability == "search_knowledge":
            # Extract search query
            match = re.search(r'(?:search|find|look up|about) (.+)', text, re.IGNORECASE)
            if match:
                params["query"] = match.group(1).strip()
        
        elif capability == "add_knowledge":
            # Try to extract key-value pair
            match = re.search(r'(?:remember|learn|store) that (.+)', text, re.IGNORECASE)
            if match:
                params["key"] = f"learned_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                params["value"] = match.group(1).strip()
        
        return params
    
    def _calculate_confidence(
        self,
        intent_type: IntentType,
        capability: Optional[str],
        cap_confidence: float
    ) -> float:
        """Calculate overall confidence score."""
        base_confidence = 0.5
        
        if intent_type != IntentType.UNKNOWN:
            base_confidence += 0.2
        
        if capability:
            base_confidence = max(base_confidence, cap_confidence)
        
        return min(1.0, base_confidence)
    
    # =========================================================================
    # Decision Making
    # =========================================================================
    
    def make_decision(
        self,
        options: List[Dict[str, Any]],
        criteria: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Make a decision between multiple options.
        
        Args:
            options: List of option dictionaries with attributes.
            criteria: Weights for different criteria (attribute: weight).
            
        Returns:
            The selected option with reasoning.
        """
        if not options:
            return {"selected": None, "reasoning": "No options available"}
        
        scored_options = []
        
        for option in options:
            score = 0.0
            for criterion, weight in criteria.items():
                value = option.get(criterion, 0)
                if isinstance(value, bool):
                    value = 1.0 if value else 0.0
                score += value * weight
            
            scored_options.append((score, option))
        
        scored_options.sort(key=lambda x: x[0], reverse=True)
        best_score, best_option = scored_options[0]
        
        self.stats["decisions_made"] += 1
        
        return {
            "selected": best_option,
            "score": best_score,
            "reasoning": f"Selected based on weighted criteria (score: {best_score:.2f})",
            "alternatives": [opt for _, opt in scored_options[1:3]],
        }
    
    # =========================================================================
    # Planning
    # =========================================================================
    
    def create_plan(
        self,
        goal: str,
        context: Dict[str, Any] = None
    ) -> List[ReasoningStep]:
        """
        Create a plan to achieve a goal.
        
        Args:
            goal: The goal to achieve.
            context: Additional context for planning.
            
        Returns:
            List of ReasoningStep objects forming the plan.
        """
        context = context or {}
        steps = []
        
        # Analyze the goal
        intent = self.analyze_intent(goal)
        
        # Step 1: Understand
        steps.append(ReasoningStep(
            step_number=1,
            action="analyze",
            reasoning=f"Analyzing goal: {goal}",
            result={"intent": intent},
        ))
        
        # Step 2: Check prerequisites
        steps.append(ReasoningStep(
            step_number=2,
            action="check_prerequisites",
            reasoning="Checking what resources and capabilities are needed",
            result={"capability": intent.get("capability")},
        ))
        
        # Step 3: Plan execution
        if intent.get("capability"):
            steps.append(ReasoningStep(
                step_number=3,
                action="execute_capability",
                reasoning=f"Execute capability: {intent['capability']}",
                result={"parameters": intent.get("parameters", {})},
            ))
        else:
            steps.append(ReasoningStep(
                step_number=3,
                action="general_response",
                reasoning="Generate appropriate response for the request",
            ))
        
        # Step 4: Verify
        steps.append(ReasoningStep(
            step_number=4,
            action="verify",
            reasoning="Verify the result meets the goal requirements",
        ))
        
        self.stats["plans_created"] += 1
        
        # Store in history
        self.reasoning_history.append({
            "timestamp": datetime.now().isoformat(),
            "goal": goal,
            "plan": [s.to_dict() for s in steps],
        })
        
        return steps
    
    def decompose_goal(
        self,
        goal: str,
        max_depth: int = 3
    ) -> Dict[str, Any]:
        """
        Decompose a complex goal into sub-goals.
        
        Args:
            goal: The main goal.
            max_depth: Maximum decomposition depth.
            
        Returns:
            Hierarchical goal structure.
        """
        # Simple rule-based decomposition
        subgoals = []
        
        # Check for compound goals (with "and", "then", etc.)
        if " and " in goal.lower():
            parts = re.split(r'\s+and\s+', goal, flags=re.IGNORECASE)
            for part in parts:
                subgoals.append({
                    "goal": part.strip(),
                    "type": "parallel",  # Can be done in parallel
                })
        elif " then " in goal.lower():
            parts = re.split(r'\s+then\s+', goal, flags=re.IGNORECASE)
            for i, part in enumerate(parts):
                subgoals.append({
                    "goal": part.strip(),
                    "type": "sequential",
                    "order": i,
                })
        else:
            subgoals.append({
                "goal": goal,
                "type": "atomic",
            })
        
        return {
            "main_goal": goal,
            "subgoals": subgoals,
            "depth": 1,
        }
    
    # =========================================================================
    # Logical Reasoning
    # =========================================================================
    
    def reason(
        self,
        premises: List[str],
        question: str
    ) -> Dict[str, Any]:
        """
        Perform logical reasoning given premises and a question.
        
        Args:
            premises: List of premise statements.
            question: The question to reason about.
            
        Returns:
            Reasoning result with conclusion.
        """
        # This is a simplified reasoning engine
        # In a full implementation, this would use more sophisticated
        # logical inference
        
        reasoning_steps = []
        
        # Step 1: Understand premises
        reasoning_steps.append({
            "step": 1,
            "action": "parse_premises",
            "result": f"Understood {len(premises)} premises",
        })
        
        # Step 2: Analyze question
        reasoning_steps.append({
            "step": 2,
            "action": "analyze_question",
            "result": f"Question type: {self._detect_intent_type(question).value}",
        })
        
        # Step 3: Search for relevant premises
        relevant = []
        question_lower = question.lower()
        for premise in premises:
            # Simple relevance check
            words = set(question_lower.split())
            premise_words = set(premise.lower().split())
            if words.intersection(premise_words):
                relevant.append(premise)
        
        reasoning_steps.append({
            "step": 3,
            "action": "find_relevant_premises",
            "result": f"Found {len(relevant)} relevant premises",
        })
        
        # Step 4: Draw conclusion
        if relevant:
            conclusion = f"Based on the premises, particularly '{relevant[0]}', the answer relates to the given information."
        else:
            conclusion = "Unable to draw a definitive conclusion from the given premises."
        
        reasoning_steps.append({
            "step": 4,
            "action": "conclude",
            "result": conclusion,
        })
        
        return {
            "premises": premises,
            "question": question,
            "relevant_premises": relevant,
            "reasoning_steps": reasoning_steps,
            "conclusion": conclusion,
            "confidence": 0.7 if relevant else 0.3,
        }
    
    # =========================================================================
    # Status
    # =========================================================================
    
    def get_status(self) -> Dict[str, Any]:
        """Get reasoning engine status."""
        return {
            "stats": self.stats.copy(),
            "reasoning_history_count": len(self.reasoning_history),
        }
