import asyncio
import os, sys
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerSSE
from dotenv import load_dotenv
import logfire
from rich.console import Console
import time
import json
import pprint

load_dotenv()

console = Console()

MODEL = os.getenv("MODEL")
MCP_SERVER_URL = "http://localhost:8000/sse"

logfire.configure(token=os.getenv("LOGFIRE_TOKEN"))
logfire.instrument_pydantic_ai()

server = MCPServerSSE(url=MCP_SERVER_URL)

# OpenAI pricing (per 1K tokens)
MODEL_COSTS = {
    "gpt-4o-mini": {"input": 0.000150, "output": 0.000600},
    "gpt-4o": {"input": 0.0025, "output": 0.01},
    "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015}
}

def debug_object(obj, name):
    """Debug any object - show type, attributes, and values"""
    console.print(f"\n[bold yellow]🔍 DEBUG: {name}[/bold yellow]")
    console.print(f"  Type: {type(obj)}")
    console.print(f"  Dir: {dir(obj)}")
    
    # Show all attributes and their values
    console.print("  Attributes:")
    for attr in dir(obj):
        if not attr.startswith('_'):  # Skip private attributes
            try:
                value = getattr(obj, attr)
                if not callable(value):  # Skip methods
                    console.print(f"    {attr}: {value} (type: {type(value)})")
            except Exception as e:
                console.print(f"    {attr}: <Error accessing: {e}>")
    
    # Try to print the object itself
    try:
        console.print(f"  Object repr: {repr(obj)}")
    except:
        console.print("  Object repr: <Error>")
    
    try:
        console.print(f"  Object str: {str(obj)}")
    except:
        console.print("  Object str: <Error>")

def calculate_cost_from_usage(usage, model):
    """Calculate cost from pydantic_ai usage object"""
    console.print("\n[bold blue]💰 COST CALCULATION DEBUG[/bold blue]")
    
    if model not in MODEL_COSTS:
        console.print(f"  ❌ Model '{model}' not in MODEL_COSTS")
        return 0.0
    
    console.print(f"  ✅ Model '{model}' found in pricing")
    console.print(f"  Pricing: {MODEL_COSTS[model]}")
    
    # Debug the usage object thoroughly
    debug_object(usage, "USAGE OBJECT")
    
    # Try different possible attribute names
    input_tokens = 0
    output_tokens = 0
    
    if hasattr(usage, 'input_tokens'):
        input_tokens = usage.input_tokens
        output_tokens = usage.output_tokens
        console.print(f"  ✅ Using input_tokens/output_tokens: {input_tokens}/{output_tokens}")
    elif hasattr(usage, 'prompt_tokens'):
        input_tokens = usage.prompt_tokens
        output_tokens = usage.completion_tokens
        console.print(f"  ✅ Using prompt_tokens/completion_tokens: {input_tokens}/{output_tokens}")
    elif hasattr(usage, 'request_tokens'):
        input_tokens = usage.request_tokens
        output_tokens = usage.response_tokens
        console.print(f"  ✅ Using request_tokens/response_tokens: {input_tokens}/{output_tokens}")
    else:
        console.print(f"  ❌ Unknown usage format!")
        return 0.0
    
    input_cost = (input_tokens / 1000) * MODEL_COSTS[model]["input"]
    output_cost = (output_tokens / 1000) * MODEL_COSTS[model]["output"]
    total_cost = input_cost + output_cost
    
    console.print(f"  Input cost: ({input_tokens}/1000) * {MODEL_COSTS[model]['input']} = ${input_cost:.6f}")
    console.print(f"  Output cost: ({output_tokens}/1000) * {MODEL_COSTS[model]['output']} = ${output_cost:.6f}")
    console.print(f"  Total cost: ${total_cost:.6f}")
    
    return total_cost

async def run_aws_agent(user_input):
    console.print("\n[bold cyan]🚀 STARTING AWS AGENT[/bold cyan]")
    
    SYSTEM_PROMPT = (
    "You are a helpful assistant for AWS management.\n"
    "Use the right tools to answer user queries as accurately as possible.\n"
    )

    user_prompt = f"{user_input}\n \
    Always try to return a valid JSON format response without using '''json '''.\n \
    Always return the result exactly the same from the MCP server, don't modify it unless explicitly asked.\n"
    
    console.print(f"System prompt length: {len(SYSTEM_PROMPT)} chars")
    console.print(f"User prompt length: {len(user_prompt)} chars")
    console.print(f"Total input length: {len(SYSTEM_PROMPT + user_prompt)} chars")
    
    # Track timing
    start_time = time.time()
    
    agent = Agent(
        name="Assistant",
        system_prompt=SYSTEM_PROMPT,
        model=MODEL,
        mcp_servers=[server]
    )
    
    console.print(f"Agent created with model: {MODEL}")
    debug_object(agent, "AGENT OBJECT")
    
    async with agent.run_mcp_servers():
        console.print("Running agent...")
        result = await agent.run(user_prompt)
        
        # Calculate metrics
        end_time = time.time()
        duration = end_time - start_time
        
        console.print(f"\n[bold green]✅ AGENT COMPLETED[/bold green]")
        console.print(f"Duration: {duration:.2f} seconds")
        
        # Debug the result object thoroughly
        debug_object(result, "RESULT OBJECT")
        
        # Get actual usage from pydantic_ai
        console.print("\n[bold blue]📊 GETTING USAGE INFO[/bold blue]")
        try:
            usage = result.usage()
            console.print("✅ Successfully got usage()")
            debug_object(usage, "USAGE FROM result.usage()")
        except Exception as e:
            console.print(f"❌ Error getting usage(): {e}")
            usage = None
        
        # Try alternative ways to get usage
        if hasattr(result, '_usage'):
            console.print("Found _usage attribute")
            debug_object(result._usage, "RESULT._USAGE")
        
        if hasattr(result, 'usage_info'):
            console.print("Found usage_info attribute")
            debug_object(result.usage_info, "RESULT.USAGE_INFO")
        
        # Calculate cost if we have usage
        actual_cost = 0.0
        if usage:
            actual_cost = calculate_cost_from_usage(usage, MODEL)
        
        # Get token info for display
        prompt_tokens = 0
        completion_tokens = 0
        total_tokens = 0
        
        if usage:
            if hasattr(usage, 'input_tokens'):
                prompt_tokens = usage.input_tokens
                completion_tokens = usage.output_tokens
                total_tokens = usage.input_tokens + usage.output_tokens
            elif hasattr(usage, 'request_tokens'):
                prompt_tokens = usage.request_tokens
                completion_tokens = usage.response_tokens
                total_tokens = usage.request_tokens + usage.response_tokens
            else:
                prompt_tokens = getattr(usage, 'prompt_tokens', 0)
                completion_tokens = getattr(usage, 'completion_tokens', 0)
                total_tokens = getattr(usage, 'total_tokens', prompt_tokens + completion_tokens)
        
        # Debug the output
        console.print(f"\n[bold magenta]📄 OUTPUT DEBUG[/bold magenta]")
        console.print(f"Output type: {type(result.output)}")
        console.print(f"Output length: {len(str(result.output))} chars")
        console.print(f"First 200 chars: {str(result.output)[:200]}...")
        
        # Build cost info with real data
        cost_info = {
            "model": MODEL,
            "duration_seconds": round(duration, 2),
            "actual_cost_usd": round(actual_cost, 6),
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "has_usage": usage is not None
        }
        
        debug_object(cost_info, "COST_INFO")
        
        return result.output, cost_info

async def main():
    user_input = sys.argv[1] if len(sys.argv) > 1 else None

    if user_input:
        console.print(f"[bold cyan]🚀 Running in CLI mode with user input:[/bold cyan] {user_input}")
        
        result, cost_info = await run_aws_agent(user_input)
        
        # Display result
        console.print(f"\n[bold green]📄 FINAL RESPONSE:[/bold green]")
        print(result)
        
        # Display cost tracking with real usage data
        console.print(f"\n[bold blue]💰 FINAL COST TRACKING:[/bold blue]")
        console.print(f"  • Model: {cost_info['model']}")
        console.print(f"  • Duration: {cost_info['duration_seconds']}s")
        console.print(f"  • Actual Cost: ${cost_info['actual_cost_usd']:.6f}")
        console.print(f"  • Tokens: {cost_info['total_tokens']} ({cost_info['prompt_tokens']} prompt + {cost_info['completion_tokens']} completion)")
        console.print(f"  • Has Usage Data: {cost_info['has_usage']}")

if __name__ == "__main__":
    asyncio.run(main())