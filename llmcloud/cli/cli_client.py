import asyncio
import sys
from rich.console import Console
from llmcloud.agent.agent import run_aws_agent
from llmcloud.agent.router_agent import CloudRouterAgent

console = Console()

async def main():

    user_input = sys.argv[1] if len(sys.argv) > 1 else None

    if not user_input:
        console.print("[red] Please provide a command[/red]")
        console.print("[yellow]Example: python3 cli_client.py 'Create an EC2 instance'[/yellow]")
        return

    console.print(f"[bold cyan] Processing request:[/bold cyan] {user_input}")

    router = CloudRouterAgent()

    try:
        result = await router.route_and_execute(user_input)
        console.print(f"[bold green]Result:[/bold green] {result.output}")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")

def main_sync():
    """Synchronous wrapper for the main function"""
    asyncio.run(main())

if __name__ == "__main__":
    main_sync()