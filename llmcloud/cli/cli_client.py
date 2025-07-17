import asyncio
import sys
from rich.console import Console
from llmcloud.agent.agent import run_aws_agent

console = Console()

async def main():

    user_input = sys.argv[1] if len(sys.argv) > 1 else None

    if user_input:
        console.print(f"[bold cyan]🚀 Running in CLI mode with user input:[/bold cyan] {user_input}")
        result = await run_aws_agent(user_input)
        print(result.output)

def main_sync():
    """Synchronous wrapper for the main function"""
    asyncio.run(main())

if __name__ == "__main__":
    main_sync()