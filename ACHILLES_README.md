# Achilles AI Assistant

<p align="center">
  <img src="https://img.shields.io/badge/version-1.0.0-blue.svg" alt="Version">
  <img src="https://img.shields.io/badge/python-3.9+-green.svg" alt="Python">
  <img src="https://img.shields.io/badge/license-MIT-orange.svg" alt="License">
</p>

**Achilles** is an advanced AI assistant framework designed for intelligent task automation, knowledge management, and research aggregation. Built with a focus on efficiency, self-improvement, and ethical operation.

## 🚀 Features

### Core Capabilities

- **🧠 Intelligent Task Management**
  - Create, prioritize, and execute tasks automatically
  - Dependency management and task chaining
  - Performance tracking and optimization

- **💾 Advanced Memory System**
  - Short-term, long-term, and episodic memory
  - Memory consolidation and importance decay
  - Semantic knowledge representation

- **🔍 Reasoning Engine**
  - Intent detection and classification
  - Goal decomposition and planning
  - Logical reasoning chains

- **⚡ Workflow Automation**
  - Visual workflow builder
  - Event and schedule triggers
  - Conditional logic and loops

- **📚 Open Research Platform**
  - Multi-source academic search (arXiv, PubMed, Semantic Scholar)
  - Government open data access
  - Patent database integration
  - Legal OSINT capabilities

- **🔧 Digital Task Execution**
  - File operations and data processing
  - Text manipulation and analysis
  - Safe execution with audit logging

- **📈 Self-Improvement**
  - Error analysis and mitigation
  - Performance optimization
  - Continuous learning

## 📦 Installation

```bash
# Basic installation
pip install -e .

# With research capabilities
pip install -e ".[research]"

# With AI provider integrations
pip install -e ".[ai]"

# Full installation
pip install -e ".[all]"
```

## 🏃 Quick Start

### Interactive Mode

```bash
python -m achilles
```

### Programmatic Usage

```python
import asyncio
from achilles import AchillesAssistant

async def main():
    # Initialize Achilles
    assistant = AchillesAssistant()
    
    # Start a conversation
    response = await assistant.chat("Hello, Achilles!")
    print(response)
    
    # Create a task
    result = await assistant._cap_create_task(
        name="Research AI Papers",
        description="Find recent papers on transformer architectures",
        priority="HIGH"
    )
    print(result)
    
    # Get system status
    status = assistant.get_full_status()
    print(status)

asyncio.run(main())
```

### Research Platform

```python
from achilles.modules.research import OpenResearchPlatform

async def research():
    platform = OpenResearchPlatform()
    
    # Search academic sources
    results = await platform.search(
        "machine learning optimization",
        categories=["ACADEMIC", "SCIENTIFIC"],
        max_results=20
    )
    
    # Generate a research report
    report = await platform.generate_report(
        "quantum computing applications"
    )
    print(report.summary)

asyncio.run(research())
```

### Workflow Automation

```python
from achilles.modules.automation import AutomationModule, TriggerType

async def automate():
    automation = AutomationModule()
    
    # Create a workflow
    workflow = automation.create_workflow(
        name="Daily Research Update",
        description="Search for new papers daily",
        trigger_type=TriggerType.SCHEDULED,
        trigger_config={"interval_seconds": 86400},
        actions=[
            {"type": "execute", "name": "search", "config": {"handler": "log", "message": "Starting research"}},
            {"type": "execute", "name": "notify", "config": {"handler": "log", "message": "Research complete"}},
        ]
    )
    
    # Execute manually
    result = await automation.execute_workflow(workflow.id)
    print(result)

asyncio.run(automate())
```

## 🏗️ Architecture

```
achilles/
├── __init__.py           # Package initialization
├── __main__.py           # CLI entry point
├── core/
│   ├── engine.py         # Core task engine
│   ├── assistant.py      # Main assistant interface
│   ├── memory.py         # Memory management
│   └── reasoning.py      # Reasoning and planning
├── modules/
│   ├── automation.py     # Workflow automation
│   ├── digital_tasks.py  # Digital task execution
│   └── research.py       # Open research platform
├── utils/
│   ├── helpers.py        # Utility functions
│   └── validators.py     # Input validation
├── config/
│   └── __init__.py       # Configuration
└── tests/
    └── test_core.py      # Test suite
```

## 📊 Available Research Sources

| Source | Category | Reliability | API |
|--------|----------|-------------|-----|
| arXiv | Academic | Verified | ✅ |
| PubMed | Scientific | Verified | ✅ |
| Semantic Scholar | Academic | Verified | ✅ |
| Crossref | Academic | Verified | ✅ |
| Data.gov | Government | Verified | ✅ |
| USPTO | Patents | Verified | ✅ |
| SEC EDGAR | Financial | Verified | ✅ |
| GitHub | Technical | High | ✅ |

## 🔒 Security & Ethics

Achilles is built with strong ethical guidelines:

- ✅ All research sources are legal and publicly accessible
- ✅ No dark web or illegal source access
- ✅ Privacy-respecting data collection
- ✅ Transparent source attribution
- ✅ Audit logging for all operations
- ✅ Safe execution with confirmation for destructive operations

## 📝 Commands

| Command | Description |
|---------|-------------|
| `help` | Show help information |
| `status` | Display system status |
| `tasks` | List all tasks |
| `create <name>` | Create a new task |
| `search <query>` | Search knowledge base |
| `research <query>` | Search research databases |
| `optimize` | Run self-optimization |
| `quit` | Exit the assistant |

## 🛠️ Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black achilles/
isort achilles/

# Type checking
mypy achilles/
```

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🤝 Contributing

Contributions are welcome! Please read the contributing guidelines before submitting pull requests.

---

<p align="center">
  <strong>Achilles</strong> - Intelligent. Efficient. Ethical.
</p>
