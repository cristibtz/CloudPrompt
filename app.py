import os, sys
import boto3
from agents import Runner, Agent
from agent.ec2_tools import create_ec2_instance, stop_ec2_instance, start_ec2_instance, list_ec2_instances, list_ec2_instance
from agents.extensions.models.litellm_model import LitellmModel

model = os.getenv("MODEL")
api_key = os.getenv("LLM_API_KEY")

if __name__ == "__main__":
    
    user_prompt = sys.argv[1]

    if not user_prompt:
        print("Please provide a user prompt.")
        sys.exit(1)

    agent = Agent(
        name="Assistant",
        instructions="You are a helpful assistant for AWS EC2 management.",
        model=LitellmModel(model=model, api_key=api_key),
        tools=[create_ec2_instance, stop_ec2_instance, start_ec2_instance, list_ec2_instances, list_ec2_instance]
    )

    response = Runner.run_sync(agent, user_prompt)
    print(response.final_output)
