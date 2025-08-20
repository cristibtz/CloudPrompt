import asyncio
import os, sys, argparse
from cloudprompt.agent.costs import calculate_cost_from_usage, agent_usage_data
from rich.console import Console
from cloudprompt.agent.router_agent import execute_provider

console = Console()

async def main():

    parser = argparse.ArgumentParser(description="CloudPrompt CLI Client")
    parser.add_argument('-p', '--prompt', required=True, type=str, help="Prompt to run")
    parser.add_argument('-c', '--cloud', required=True, type=str, help="Cloud provider to use (e.g., 'aws', 'gcp', 'azure', 'proxmox')")

    aws_group = parser.add_argument_group('AWS credentials')
    aws_group.add_argument('--aws-access-key', type=str, help="AWS Access Key ID")
    aws_group.add_argument('--aws-secret-key', type=str, help="AWS Secret Access Key")

    proxmox_group = parser.add_argument_group('Proxmox credentials')
    proxmox_group.add_argument('--proxmox-host', type=str, help="Proxmox host")
    proxmox_group.add_argument('--proxmox-username', type=str, help="Proxmox username")
    proxmox_group.add_argument('--proxmox-password', type=str, help="Proxmox password")

    args = parser.parse_args()

    credentials = {}
    if args.cloud == 'aws':
        credentials = {
            'access_key': args.aws_access_key or os.getenv('AWS_ACCESS_KEY_ID'),
            'secret_key': args.aws_secret_key or os.getenv('AWS_SECRET_ACCESS_KEY'),
        }
    elif args.cloud == 'proxmox':
        credentials = {
            'host': args.proxmox_host or os.getenv('PROXMOX_HOST'),
            'username': args.proxmox_username or os.getenv('PROXMOX_USER'),
            'password': args.proxmox_password or os.getenv('PROXMOX_PASS')
        }

    user_input = args.prompt
    cloud_provider = args.cloud

    console.print(f"[bold cyan] Processing request:[/bold cyan] {user_input}")

    try:
        result = await execute_provider(cloud_provider, user_input, credentials)
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