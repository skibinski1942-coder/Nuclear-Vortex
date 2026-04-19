# Nuclear-Vortex

**A brand that leads in the world of confused with clarity.**

Nuclear-Vortex is a technology holding company built on a single conviction: _technology should make human life simpler, not harder_. We cut through the noise, turn complexity into clarity, and deliver products that just work — for everyone.

---

## Vision

> To be the world's most human-centered technology conglomerate — growing extraordinary wealth by delivering extraordinary simplicity.

## Mission

Build a portfolio of companies that each solve one hard, human problem with elegant, accessible technology — and in doing so, create lasting value for users, employees, and investors.

---

## The Nuclear-Vortex Family

| Sub-Company | Focus | Tagline |
|---|---|---|
| **ClarityTech** | Human-centered UI/UX & OS platform | *See clearly. Think simply.* |
| **Vortex Ventures** | Financial technology & wealth operations | *Your money, amplified.* |
| **Nova Labs** | Research & Development / Innovation hub | *Tomorrow's answers, today.* |

---

## 🏛️ Achilles AI Assistant

This repository also contains **Achilles**, an advanced AI assistant framework designed for:

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

---

## Java Multi-Module Project Structure

The sub-company platform is a Maven multi-module project. Each sub-company lives in its own module:

```
Nuclear-Vortex/
├── nuclear-vortex-core/     # Shared company model, interfaces, and utilities
├── clarity-tech/            # ClarityTech — simplicity platform
├── vortex-ventures/         # Vortex Ventures — financial technology
└── nova-labs/               # Nova Labs — R&D and innovation
```

### Building

```bash
mvn clean install
```

### Testing

```bash
mvn test
```

---

## Core Principles

1. **Clarity over complexity** — every product we ship must be understandable by anyone.
2. **Innovation through simplicity** — the best technology disappears into the background.
3. **Wealth through value** — we grow by genuinely helping people.
4. **Open by default** — our foundational platform is open-source (GPL v2).

---

## License

GNU General Public License v2 — see [LICENSE](LICENSE).
