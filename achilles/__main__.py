#!/usr/bin/env python3
"""
Achilles AI Assistant - Main Entry Point
========================================

Usage:
    python -m achilles                    # Start interactive mode
    python -m achilles --status           # Show system status
    python -m achilles --help             # Show help
    
Or use programmatically:
    from achilles import AchillesAssistant
    
    assistant = AchillesAssistant()
    response = await assistant.chat("Hello!")
"""

import asyncio
import argparse
import logging
import sys
from typing import Optional

from achilles.core.assistant import AchillesAssistant
from achilles.config import DEFAULT_CONFIG


def setup_logging(level: str = "INFO") -> None:
    """Configure logging."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )


def print_banner() -> None:
    """Print the Achilles banner."""
    banner = """
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║     █████╗  ██████╗██╗  ██╗██╗██╗     ██╗     ███████╗███████╗║
    ║    ██╔══██╗██╔════╝██║  ██║██║██║     ██║     ██╔════╝██╔════╝║
    ║    ███████║██║     ███████║██║██║     ██║     █████╗  ███████╗║
    ║    ██╔══██║██║     ██╔══██║██║██║     ██║     ██╔══╝  ╚════██║║
    ║    ██║  ██║╚██████╗██║  ██║██║███████╗███████╗███████╗███████║║
    ║    ╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚═╝╚══════╝╚══════╝╚══════╝╚══════╝║
    ║                                                               ║
    ║              Advanced AI Assistant Framework                  ║
    ║                       Version 1.0.0                           ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def print_help() -> None:
    """Print help information."""
    help_text = """
    Achilles AI Assistant - Help
    ============================
    
    Commands (in interactive mode):
    
      help                  Show this help message
      status                Show system status
      tasks                 List all tasks
      create <name>         Create a new task
      search <query>        Search the knowledge base
      research <query>      Search research databases
      optimize              Run self-optimization
      export                Export system state
      quit / exit           Exit the assistant
    
    Capabilities:
    
      - Task Management: Create, prioritize, and execute tasks
      - Knowledge Management: Store and retrieve information
      - Workflow Automation: Create automated workflows
      - Research Platform: Search academic and open data sources
      - Digital Task Execution: Automate digital tasks safely
      - Self-Improvement: Continuous learning and optimization
    
    Examples:
    
      > create task "Review AI papers"
      > search machine learning
      > research quantum computing papers
      > status
    
    For more information, visit the documentation.
    """
    print(help_text)


async def interactive_mode(assistant: AchillesAssistant) -> None:
    """Run the assistant in interactive mode."""
    print_banner()
    print("\n    Type 'help' for commands, 'quit' to exit.\n")
    
    while True:
        try:
            user_input = input("    You > ").strip()
            
            if not user_input:
                continue
            
            # Handle commands
            if user_input.lower() in ["quit", "exit", "q"]:
                print("\n    Goodbye! Achilles signing off.\n")
                break
            
            elif user_input.lower() == "help":
                print_help()
                continue
            
            elif user_input.lower() == "status":
                status = assistant.get_full_status()
                print(f"\n    System Status:")
                print(f"    - Engine: {status['engine']['metrics']['success_rate']}% success rate")
                print(f"    - Tasks Completed: {status['engine']['metrics']['tasks_completed']}")
                print(f"    - Knowledge Entries: {status['engine']['metrics']['knowledge_entries']}")
                print(f"    - Memory Status: {status['memory']['short_term_count']} short-term, {status['memory']['long_term_count']} long-term")
                print()
                continue
            
            elif user_input.lower() == "optimize":
                report = assistant.engine.self_optimize()
                print(f"\n    Optimization complete. {len(report['actions'])} actions performed.\n")
                continue
            
            # Regular conversation
            response = await assistant.chat(user_input)
            print(f"\n    Achilles > {response}\n")
            
        except KeyboardInterrupt:
            print("\n\n    Interrupted. Type 'quit' to exit.\n")
        except Exception as e:
            print(f"\n    Error: {e}\n")


def show_status(assistant: AchillesAssistant) -> None:
    """Show system status."""
    status = assistant.get_full_status()
    
    print("\n=== Achilles System Status ===\n")
    
    print("Engine:")
    for key, value in status["engine"]["metrics"].items():
        print(f"  {key}: {value}")
    
    print("\nMemory:")
    for key, value in status["memory"].items():
        print(f"  {key}: {value}")
    
    print("\nCapabilities:")
    for cap in status["assistant"]["registered_capabilities"]:
        print(f"  - {cap}")
    
    print()


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Achilles AI Assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m achilles                    Start interactive mode
  python -m achilles --status           Show system status
  python -m achilles --query "Hello"    Send a single query
        """
    )
    
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show system status"
    )
    parser.add_argument(
        "--query", "-q",
        type=str,
        help="Send a single query"
    )
    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level"
    )
    parser.add_argument(
        "--version",
        action="version",
        version="Achilles AI Assistant v1.0.0"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    
    # Load configuration
    config = DEFAULT_CONFIG.copy()
    
    # Initialize assistant
    assistant = AchillesAssistant(config=config)
    
    # Handle commands
    if args.status:
        show_status(assistant)
    elif args.query:
        response = asyncio.run(assistant.chat(args.query))
        print(f"Achilles: {response}")
    else:
        # Interactive mode
        asyncio.run(interactive_mode(assistant))


if __name__ == "__main__":
    main()
