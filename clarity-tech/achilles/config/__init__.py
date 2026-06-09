"""
Achilles Configuration
======================

Default configuration and settings for the Achilles AI Assistant.
"""

# Default configuration
DEFAULT_CONFIG = {
    "version": "1.0.0",
    
    # Core Engine Settings
    "engine": {
        "max_concurrent_tasks": 10,
        "task_timeout": 300,  # seconds
        "auto_optimize_interval": 3600,  # 1 hour
    },
    
    # Memory Settings
    "memory": {
        "short_term_capacity": 100,
        "max_long_term": 10000,
        "consolidation_threshold": 3,
        "importance_decay": 0.01,
    },
    
    # Reasoning Settings
    "reasoning": {
        "max_planning_depth": 5,
        "confidence_threshold": 0.6,
    },
    
    # Automation Settings
    "automation": {
        "max_workflow_steps": 50,
        "max_concurrent_workflows": 5,
        "default_timeout": 60,
    },
    
    # Digital Task Executor Settings
    "digital_tasks": {
        "require_confirmation_for": ["delete", "modify", "send", "execute"],
        "allowed_read_dirs": ["."],
        "allowed_write_dirs": ["."],
        "max_file_size": 10485760,  # 10MB
    },
    
    # Research Platform Settings
    "research": {
        "cache_ttl": 3600,  # 1 hour
        "max_results_per_source": 100,
        "default_reliability_threshold": "MEDIUM",
        "rate_limit_buffer": 0.1,  # 10% buffer on rate limits
    },
    
    # AI Provider Settings
    "ai_provider": {
        "type": "local",  # local, openai, anthropic, etc.
        "model": "default",
        "temperature": 0.7,
        "max_tokens": 2048,
    },
    
    # Logging Settings
    "logging": {
        "level": "INFO",
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    },
    
    # Security Settings
    "security": {
        "audit_logging": True,
        "max_audit_entries": 10000,
        "sanitize_inputs": True,
    },
}


# Research source configurations
RESEARCH_SOURCES = {
    "arxiv": {
        "name": "arXiv",
        "base_url": "http://export.arxiv.org/api/query",
        "rate_limit": 3,  # requests per second
        "categories": ["physics", "math", "cs", "q-bio", "q-fin", "stat", "eess", "econ"],
    },
    "pubmed": {
        "name": "PubMed",
        "base_url": "https://eutils.ncbi.nlm.nih.gov/entrez/eutils",
        "rate_limit": 3,
    },
    "semantic_scholar": {
        "name": "Semantic Scholar",
        "base_url": "https://api.semanticscholar.org/graph/v1",
        "rate_limit": 100,
        "requires_key": True,
    },
    "crossref": {
        "name": "Crossref",
        "base_url": "https://api.crossref.org",
        "rate_limit": 50,
    },
    "github": {
        "name": "GitHub",
        "base_url": "https://api.github.com",
        "rate_limit": 60,  # unauthenticated
        "requires_key": True,  # for higher limits
    },
}


# Capability definitions for documentation
CAPABILITIES = {
    "task_management": {
        "name": "Task Management",
        "description": "Create, prioritize, and execute tasks automatically",
        "methods": ["create_task", "list_tasks", "execute_task", "prioritize_tasks"],
    },
    "knowledge_management": {
        "name": "Knowledge Management",
        "description": "Store, retrieve, and search knowledge",
        "methods": ["add_knowledge", "get_knowledge", "search_knowledge"],
    },
    "automation": {
        "name": "Workflow Automation",
        "description": "Create and execute automated workflows",
        "methods": ["create_workflow", "execute_workflow", "schedule_workflow"],
    },
    "research": {
        "name": "Research Platform",
        "description": "Search and aggregate research from multiple sources",
        "methods": ["search", "generate_report", "osint_lookup"],
    },
    "digital_tasks": {
        "name": "Digital Task Execution",
        "description": "Execute digital tasks with safety controls",
        "methods": ["create_task", "plan_execution", "execute_task"],
    },
    "self_improvement": {
        "name": "Self-Improvement",
        "description": "Analyze performance and optimize operations",
        "methods": ["analyze_errors", "self_optimize", "apply_improvement"],
    },
}
