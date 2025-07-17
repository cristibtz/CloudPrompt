import asyncio
import os, sys
from shared import run_aws_agent, agent_usage_data
from rich.console import Console

console = Console()

async def main():
    user_input = sys.argv[1] if len(sys.argv) > 1 else None

    if user_input:
        console.print(f"[bold cyan]🚀 Running in CLI mode with user input:[/bold cyan] {user_input}")
        
        result = await run_aws_agent(user_input)

        cost_info = agent_usage_data(result)
        
        # Display result
        console.print(f"\n[bold green]📄 FINAL RESPONSE:[/bold green]")
        print(result)
        
        # Display cost tracking with real usage data
        console.print(f"\n[bold blue]💰 FINAL COST TRACKING:[/bold blue]")
        console.print(f"  • Model: {cost_info['model']}")
        console.print(f"  • Actual Cost: ${cost_info['actual_cost_usd']:.6f}")
        console.print(f"  • Tokens: {cost_info['total_tokens']} ({cost_info['prompt_tokens']} prompt + {cost_info['completion_tokens']} completion)")
        console.print(f"  • Has Usage Data: {cost_info['has_usage']}")

if __name__ == "__main__":
    asyncio.run(main())