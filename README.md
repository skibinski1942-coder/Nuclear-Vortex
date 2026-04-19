# Nuclear-Vortex

A brand that leads in the world of confused with clarity

## 🏛️ Achilles AI Assistant

This repository contains **Achilles**, an advanced AI assistant framework designed for:

- 🧠 **Intelligent Task Management** - Create, prioritize, and execute tasks automatically
- 📚 **Open Research Platform** - Search academic databases, government data, and patents
- ⚡ **Workflow Automation** - Build and execute automated workflows
- 💾 **Knowledge Management** - Store, retrieve, and learn from information
- 📈 **Self-Improvement** - Continuous optimization and learning

### Quick Start

```bash
# Install
pip install -e .

# Run interactive mode
python -m achilles

# Or use programmatically
python -c "
import asyncio
from achilles import AchillesAssistant

async def main():
    assistant = AchillesAssistant()
    response = await assistant.chat('Hello!')
    print(response)

asyncio.run(main())
"
```

### Documentation

See [ACHILLES_README.md](ACHILLES_README.md) for full documentation.

### Architecture

```
achilles/
├── core/           # Core engine, assistant, memory, reasoning
├── modules/        # Automation, research, digital tasks
├── utils/          # Helpers and validators
├── config/         # Configuration
└── tests/          # Test suite
```

### License

MIT License
