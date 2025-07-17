import os, time
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerSSE
from dotenv import load_dotenv
import logfire
from rich.console import Console

console = Console()

load_dotenv()

MODEL = os.getenv("MODEL")
MCP_SERVER_URL = "http://localhost:8000/sse"

logfire.configure(token=os.getenv("LOGFIRE_TOKEN"))
logfire.instrument_pydantic_ai()

server = MCPServerSSE(url=MCP_SERVER_URL)

# Define Model costs
MODEL_COSTS = {
    "gpt-4o-mini": {"input": 0.000150, "output": 0.000600},
}

# AWS agent
async def run_aws_agent(user_input):
    """Shared AWS agent function"""
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

    start_time = time.time()

    agent = Agent(
        name="Assistant",
        system_prompt=SYSTEM_PROMPT,
        model=MODEL,
        mcp_servers=[server]
    )
    
    async with agent.run_mcp_servers():
        console.print("Running agent...")

        result = await agent.run(user_prompt)

        end_time = time.time()
        duration = end_time - start_time

        console.print(f"\n[bold green]✅ AGENT COMPLETED[/bold green]")
        console.print(f"Duration: {duration:.2f} seconds")

        return result

# Cost debugging and monitoring
def agent_usage_data(result):
    console.print("\n[bold blue]📊 GETTING USAGE INFO[/bold blue]")

    try:
        usage = result.usage()
        print(result.usage())
        console.print("✅ Successfully got usage()")
    except Exception as e:
        console.print(f"❌ Error getting usage(): {e}")
        usage = None   
    
    actual_cost = 0.0
    if usage:
        actual_cost = calculate_cost_from_usage(usage, MODEL)
    
    prompt_tokens = 0
    completion_tokens = 0
    total_tokens = 0
    
    prompt_tokens = usage.request_tokens
    completion_tokens = usage.response_tokens
    total_tokens = usage.request_tokens + usage.response_tokens
    
    # Build cost info with real data
    cost_info = {
        "model": MODEL,
        "actual_cost_usd": round(actual_cost, 6),
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "has_usage": usage is not None
    }
            
    return cost_info

def calculate_cost_from_usage(usage, model):
    """Calculate cost from pydantic_ai usage object"""
    
    if model not in MODEL_COSTS:
        console.print(f"  ❌ Model '{model}' not in MODEL_COSTS")
        return 0.0
    
    console.print(f"  ✅ Model '{model}' found in pricing")
    console.print(f"  Pricing: {MODEL_COSTS[model]}")
        
    # Try different possible attribute names
    input_tokens = 0
    output_tokens = 0
    
    input_tokens = usage.request_tokens
    output_tokens = usage.response_tokens
    console.print(f"  ✅ Using request_tokens/response_tokens: {input_tokens}/{output_tokens}")
    
    input_cost = (input_tokens / 1000) * MODEL_COSTS[model]["input"]
    output_cost = (output_tokens / 1000) * MODEL_COSTS[model]["output"]
    total_cost = input_cost + output_cost
    
    console.print(f"  Input cost: ({input_tokens}/1000) * {MODEL_COSTS[model]['input']} = ${input_cost:.6f}")
    console.print(f"  Output cost: ({output_tokens}/1000) * {MODEL_COSTS[model]['output']} = ${output_cost:.6f}")
    console.print(f"  Total cost: ${total_cost:.6f}")
    
    return total_cost