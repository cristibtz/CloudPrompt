from rich.console import Console
from cloudprompt.agent.agent import run_aws_agent
from dotenv import load_dotenv
import os

load_dotenv()

MODEL = os.getenv("MODEL")

# Define Model costs per 1000 tokens
MODEL_COSTS = {
    "claude-4-sonnet": {"input": 0.003, "output": 0.015},
    "gpt-5-mini" : {"input": 0.000250, "output": 0.002},
    "gpt-4o-mini": {"input": 0.000150, "output": 0.000600}, # Best
    "gpt-4.1-nano":{ "input": 0.00010, "output": 0.000400},
    "o3-mini": {"input": 0.0011, "output": 0.0044},
}

console = Console()

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