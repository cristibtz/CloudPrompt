import os, sys
import boto3
from dotenv import load_dotenv
from agents import Runner, Agent
from agent.ec2_tools import create_ec2_instance, stop_ec2_instance, start_ec2_instance, list_ec2_instances, list_ec2_instance

load_dotenv()

if __name__ == "__main__":
    
    user_prompt = sys.argv[1]

    if not user_prompt:
        print("Please provide a user prompt.")
        sys.exit(1)

    agent = Agent(
        name="Assistant",
        instructions="You are a helpful assistant for AWS EC2 management.",
        tools=[create_ec2_instance, stop_ec2_instance, start_ec2_instance, list_ec2_instances, list_ec2_instance]
    )

    response = Runner.run_sync(agent, user_prompt)
    print(response.final_output)
