import asyncio
import os, sys
from llmcloud.agent.agent import run_aws_agent
from llmcloud.agent.costs import calculate_cost_from_usage, agent_usage_data
from llmcloud.agent.router_agent import CloudRouterAgent
from rich.console import Console

console = Console()

async def main():
    user_input = sys.argv[1] if len(sys.argv) > 1 else None

    if not user_input:
        console.print("[red] Please provide a command[/red]")
        console.print("[yellow]Example: python3 cli_client.py 'Create an EC2 instance'[/yellow]")
        return

    console.print(f"[bold cyan]🚀 Running in CLI mode with user input:[/bold cyan] {user_input}")
    
    
    console.print(f"[bold cyan] Processing request:[/bold cyan] {user_input}")

    router = CloudRouterAgent()

    try:
        result = await router.route_and_execute(user_input)
        try:
            cost_info = agent_usage_data(result)
        except Exception as e:
            console.print(f"[bold red]Error calculating cost data:[/bold red] {str(e)}")
            cost_info = {
                'model': 'unknown',
                'actual_cost_usd': 0.0,
                'total_tokens': 0,
                'prompt_tokens': 0,
                'completion_tokens': 0,
                'has_usage': False
            }
        console.print(f"[bold green]Result:[/bold green] {result.output}")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")

    # Display result
    console.print(f"\n[bold green]📄 FINAL RESPONSE:[/bold green]")
    print(result.output)
    
    # Display cost tracking with real usage data
    console.print(f"\n[bold blue]💰 FINAL COST TRACKING:[/bold blue]")
    console.print(f"  • Model: {cost_info['model']}")
    console.print(f"  • Actual Cost: ${cost_info['actual_cost_usd']:.6f}")
    console.print(f"  • Tokens: {cost_info['total_tokens']} ({cost_info['prompt_tokens']} prompt + {cost_info['completion_tokens']} completion)")
    console.print(f"  • Has Usage Data: {cost_info['has_usage']}")

if __name__ == "__main__":
    asyncio.run(main())