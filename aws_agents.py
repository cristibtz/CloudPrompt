from agents import Agent
from tools import create_ec2_vm, stop_ec2_vm

ec2_creation_agent = Agent(
    name="Assistant", 
    instructions="You are a helpful prompt parser assistant, tasked with parsing user prompts related to AWS EC2 instance creation and generating appropriate JSON objects.", 
    model="gpt-4.1-nano",
    tools=[create_ec2_vm]
)

ec2_stopping_agent = Agent(
    name="Assistant", 
    instructions="You are a helpful prompt parser assistant, tasked with parsing user prompts related to AWS EC2 instance stopping.", 
    model="gpt-4.1-nano",
    tools=[stop_ec2_vm]
)
