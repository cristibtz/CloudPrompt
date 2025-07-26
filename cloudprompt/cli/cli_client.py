import asyncio
import os, sys, argparse
from cloudprompt.agent.costs import calculate_cost_from_usage, agent_usage_data
from rich.console import Console
from cloudprompt.agent.agent import run_aws_agent
from cloudprompt.agent.router_agent import CloudRouterAgent

console = Console()

async def main():

    parser = argparse.ArgumentParser(description="CloudPrompt CLI Client")
    parser.add_argument('-p', '--prompt', required=True, type=str, help="Prompt to run")

    args = parser.parse_args()
    user_input = args.prompt

    console.print(f"[bold cyan] Processing request:[/bold cyan] {user_input}")

    router = CloudRouterAgent()

    try:
        result = await router.route_and_execute(user_input)
        # Debug
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
    
    # Debug
    # Display result
    console.print(f"\n[bold green]📄 FINAL RESPONSE:[/bold green]")
    print(result.output)
    
    # Display cost tracking with real usage data
    console.print(f"\n[bold blue]💰 FINAL COST TRACKING:[/bold blue]")
    console.print(f"  • Model: {cost_info['model']}")
    console.print(f"  • Actual Cost: ${cost_info['actual_cost_usd']:.6f}")
    console.print(f"  • Tokens: {cost_info['total_tokens']} ({cost_info['prompt_tokens']} prompt + {cost_info['completion_tokens']} completion)")
    console.print(f"  • Has Usage Data: {cost_info['has_usage']}")

def main_sync():
    """Synchronous wrapper for the main function"""
    asyncio.run(main())

if __name__ == "__main__":
    main_sync()