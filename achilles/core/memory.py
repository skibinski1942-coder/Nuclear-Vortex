"""
Achilles Memory System
======================

Manages short-term, long-term, and episodic memory for
learning, context retention, and knowledge accumulation.
"""

import json
import logging
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class MemoryEntry:
    """Represents a single memory entry."""
    id: str
    content: Any
    memory_type: str  # short_term, long_term, episodic
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    importance: float = 0.5
    tags: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "memory_type": self.memory_type,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
            "access_count": self.access_count,
            "importance": self.importance,
            "tags": self.tags,
            "context": self.context,
        }


class MemorySystem:
    """
    Comprehensive memory management system for Achilles.
    
    Features:
    - Short-term memory: Recent context and working memory
    - Long-term memory: Persistent knowledge and learnings
    - Episodic memory: Conversation and interaction history
    - Semantic memory: Concepts and relationships
    - Memory consolidation: Moving important short-term to long-term
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Memory System.
        
        Args:
            config: Memory configuration settings.
        """
        self.config = config or {}
        
        # Memory stores
        self.short_term: deque = deque(
            maxlen=self.config.get("short_term_capacity", 100)
        )
        self.long_term: Dict[str, MemoryEntry] = {}
        self.episodic: List[MemoryEntry] = []
        self.semantic: Dict[str, Dict[str, Any]] = {}
        
        # Memory indices for fast lookup
        self._tag_index: Dict[str, List[str]] = {}
        self._content_hash_index: Dict[str, str] = {}
        
        # Statistics
        self.stats = {
            "total_memories": 0,
            "consolidations": 0,
            "retrievals": 0,
            "forgettings": 0,
        }
        
        # Configuration
        self.consolidation_threshold = self.config.get("consolidation_threshold", 3)
        self.importance_decay = self.config.get("importance_decay", 0.01)
        self.max_long_term = self.config.get("max_long_term", 10000)
        
        logger.info("Memory System initialized")
    
    def _generate_id(self, content: Any) -> str:
        """Generate a unique ID for memory content."""
        content_str = json.dumps(content, sort_keys=True, default=str)
        hash_obj = hashlib.sha256(content_str.encode())
        return f"mem_{hash_obj.hexdigest()[:12]}"
    
    # =========================================================================
    # Memory Operations
    # =========================================================================
    
    def remember(
        self,
        content: Any,
        memory_type: str = "short_term",
        importance: float = 0.5,
        tags: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> MemoryEntry:
        """
        Store a new memory.
        
        Args:
            content: The content to remember.
            memory_type: Type of memory (short_term, long_term, episodic).
            importance: Importance score (0-1).
            tags: Tags for categorization.
            context: Additional context.
            
        Returns:
            The created MemoryEntry.
        """
        now = datetime.now()
        memory_id = self._generate_id(content)
        
        # Check for duplicates
        if memory_id in self._content_hash_index:
            existing_id = self._content_hash_index[memory_id]
            if existing_id in self.long_term:
                existing = self.long_term[existing_id]
                existing.access_count += 1
                existing.last_accessed = now
                existing.importance = min(1.0, existing.importance + 0.1)
                return existing
        
        entry = MemoryEntry(
            id=memory_id,
            content=content,
            memory_type=memory_type,
            created_at=now,
            last_accessed=now,
            importance=importance,
            tags=tags or [],
            context=context or {},
        )
        
        # Store based on type
        if memory_type == "short_term":
            self.short_term.append(entry)
        elif memory_type == "long_term":
            self.long_term[memory_id] = entry
        elif memory_type == "episodic":
            self.episodic.append(entry)
        
        # Update indices
        self._content_hash_index[memory_id] = memory_id
        for tag in entry.tags:
            if tag not in self._tag_index:
                self._tag_index[tag] = []
            self._tag_index[tag].append(memory_id)
        
        self.stats["total_memories"] += 1
        logger.debug(f"Stored memory: {memory_id} ({memory_type})")
        
        return entry
    
    def recall(
        self,
        query: str = None,
        tags: List[str] = None,
        memory_type: str = None,
        limit: int = 10
    ) -> List[MemoryEntry]:
        """
        Recall memories matching criteria.
        
        Args:
            query: Text query to search for.
            tags: Tags to filter by.
            memory_type: Type of memory to search.
            limit: Maximum results to return.
            
        Returns:
            List of matching MemoryEntry objects.
        """
        results = []
        candidates = []
        
        # Gather candidates based on memory type
        if memory_type == "short_term" or memory_type is None:
            candidates.extend(list(self.short_term))
        if memory_type == "long_term" or memory_type is None:
            candidates.extend(list(self.long_term.values()))
        if memory_type == "episodic" or memory_type is None:
            candidates.extend(self.episodic)
        
        # Filter by tags
        if tags:
            tag_set = set(tags)
            candidates = [
                c for c in candidates
                if tag_set.intersection(set(c.tags))
            ]
        
        # Filter by query
        if query:
            query_lower = query.lower()
            filtered = []
            for c in candidates:
                content_str = str(c.content).lower()
                if query_lower in content_str:
                    filtered.append(c)
            candidates = filtered
        
        # Sort by importance and recency
        candidates.sort(
            key=lambda x: (x.importance, x.last_accessed),
            reverse=True
        )
        
        results = candidates[:limit]
        
        # Update access stats
        now = datetime.now()
        for entry in results:
            entry.last_accessed = now
            entry.access_count += 1
        
        self.stats["retrievals"] += 1
        return results
    
    def forget(
        self,
        memory_id: str = None,
        older_than: timedelta = None,
        importance_below: float = None
    ) -> int:
        """
        Forget (remove) memories matching criteria.
        
        Args:
            memory_id: Specific memory to forget.
            older_than: Remove memories older than this duration.
            importance_below: Remove memories below this importance.
            
        Returns:
            Number of memories forgotten.
        """
        forgotten = 0
        now = datetime.now()
        
        if memory_id:
            if memory_id in self.long_term:
                del self.long_term[memory_id]
                forgotten += 1
        else:
            # Forget from long-term based on criteria
            to_remove = []
            for mid, entry in self.long_term.items():
                remove = False
                
                if older_than and (now - entry.created_at) > older_than:
                    remove = True
                if importance_below and entry.importance < importance_below:
                    remove = True
                
                if remove:
                    to_remove.append(mid)
            
            for mid in to_remove:
                del self.long_term[mid]
                forgotten += 1
        
        self.stats["forgettings"] += forgotten
        logger.info(f"Forgot {forgotten} memories")
        return forgotten
    
    # =========================================================================
    # Memory Consolidation
    # =========================================================================
    
    def consolidate(self) -> Dict[str, Any]:
        """
        Consolidate important short-term memories to long-term.
        
        Returns:
            Consolidation report.
        """
        consolidated = 0
        
        for entry in list(self.short_term):
            # Check if should consolidate
            should_consolidate = (
                entry.access_count >= self.consolidation_threshold or
                entry.importance >= 0.7
            )
            
            if should_consolidate:
                # Move to long-term
                entry.memory_type = "long_term"
                self.long_term[entry.id] = entry
                consolidated += 1
        
        # Apply importance decay to long-term memories
        for entry in self.long_term.values():
            entry.importance = max(0.1, entry.importance - self.importance_decay)
        
        # Prune if over capacity
        if len(self.long_term) > self.max_long_term:
            self._prune_long_term()
        
        self.stats["consolidations"] += 1
        
        report = {
            "consolidated": consolidated,
            "long_term_count": len(self.long_term),
            "short_term_count": len(self.short_term),
        }
        
        logger.info(f"Consolidation complete: {consolidated} memories moved")
        return report
    
    def _prune_long_term(self) -> None:
        """Remove lowest importance long-term memories."""
        if len(self.long_term) <= self.max_long_term:
            return
        
        # Sort by importance
        sorted_entries = sorted(
            self.long_term.items(),
            key=lambda x: x[1].importance
        )
        
        # Remove lowest importance
        to_remove = len(self.long_term) - self.max_long_term
        for mid, _ in sorted_entries[:to_remove]:
            del self.long_term[mid]
            self.stats["forgettings"] += 1
    
    # =========================================================================
    # Semantic Memory
    # =========================================================================
    
    def add_concept(
        self,
        concept: str,
        definition: str,
        relationships: Optional[Dict[str, List[str]]] = None
    ) -> None:
        """
        Add a semantic concept.
        
        Args:
            concept: The concept name.
            definition: Definition of the concept.
            relationships: Related concepts (e.g., {"is_a": ["thing"], "has": ["property"]})
        """
        self.semantic[concept] = {
            "definition": definition,
            "relationships": relationships or {},
            "created_at": datetime.now().isoformat(),
        }
        logger.debug(f"Added concept: {concept}")
    
    def get_concept(self, concept: str) -> Optional[Dict[str, Any]]:
        """Get a semantic concept."""
        return self.semantic.get(concept)
    
    def find_related_concepts(self, concept: str) -> List[str]:
        """Find concepts related to the given concept."""
        if concept not in self.semantic:
            return []
        
        related = []
        entry = self.semantic[concept]
        
        for rel_type, concepts in entry.get("relationships", {}).items():
            related.extend(concepts)
        
        return list(set(related))
    
    # =========================================================================
    # Interaction Memory
    # =========================================================================
    
    def add_interaction(
        self,
        user_input: str,
        assistant_response: str,
        intent: Dict[str, Any]
    ) -> MemoryEntry:
        """
        Record an interaction for learning.
        
        Args:
            user_input: What the user said.
            assistant_response: How the assistant responded.
            intent: Detected intent information.
            
        Returns:
            The created memory entry.
        """
        content = {
            "user_input": user_input,
            "assistant_response": assistant_response,
            "intent": intent,
        }
        
        # Determine importance based on intent
        importance = 0.5
        if intent.get("is_capability_request"):
            importance = 0.7
        if intent.get("is_feedback"):
            importance = 0.8
        if intent.get("is_correction"):
            importance = 0.9
        
        return self.remember(
            content=content,
            memory_type="episodic",
            importance=importance,
            tags=["interaction", intent.get("capability", "general")],
            context={"timestamp": datetime.now().isoformat()},
        )
    
    # =========================================================================
    # Status and Export
    # =========================================================================
    
    def get_status(self) -> Dict[str, Any]:
        """Get memory system status."""
        return {
            "short_term_count": len(self.short_term),
            "long_term_count": len(self.long_term),
            "episodic_count": len(self.episodic),
            "semantic_concepts": len(self.semantic),
            "stats": self.stats.copy(),
        }
    
    def export_state(self) -> Dict[str, Any]:
        """Export complete memory state."""
        return {
            "version": "1.0.0",
            "exported_at": datetime.now().isoformat(),
            "short_term": [e.to_dict() for e in self.short_term],
            "long_term": {k: v.to_dict() for k, v in self.long_term.items()},
            "episodic": [e.to_dict() for e in self.episodic],
            "semantic": self.semantic,
            "stats": self.stats,
        }
    
    def import_state(self, state: Dict[str, Any]) -> None:
        """Import previously exported state."""
        # Restore long-term memories
        for mid, data in state.get("long_term", {}).items():
            entry = MemoryEntry(
                id=data["id"],
                content=data["content"],
                memory_type="long_term",
                created_at=datetime.fromisoformat(data["created_at"]),
                last_accessed=datetime.fromisoformat(data["last_accessed"]),
                access_count=data["access_count"],
                importance=data["importance"],
                tags=data["tags"],
                context=data["context"],
            )
            self.long_term[mid] = entry
        
        # Restore semantic memory
        self.semantic = state.get("semantic", {})
        
        # Restore stats
        self.stats.update(state.get("stats", {}))
        
        logger.info("Memory state imported")
