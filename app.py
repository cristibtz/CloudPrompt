import os, sys
import boto3
from dotenv import load_dotenv
from agents import Runner, Agent
from aws_agents import ec2_creation_agent, ec2_stopping_agent
from tools import create_ec2_vm, stop_ec2_vm

load_dotenv()

if __name__ == "__main__":
    
    user_prompt = sys.argv[1]

    if not user_prompt:
        print("Please provide a user prompt.")
        sys.exit(1)

    agent = Agent(
        name="Assistant",
        instructions="You are a helpful assistant for AWS EC2 management.",
        tools=[create_ec2_vm, stop_ec2_vm]
    )

    response = Runner.run_sync(agent, user_prompt)
    print(response.final_output)
