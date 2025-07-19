from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda
from llmcloud.agent.agent import run_aws_agent, run_azure_agent, run_gcp_agent
import os

class CloudRouterAgent:
    def __init__(self):
        self.model = ChatOpenAI(
            model=os.getenv("MODEL", "gpt-4o-mini"),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
        )

        self.router_prompt = PromptTemplate.from_template(
            """
            You are a cloud provider routing assistant. Based on the user's input, decide which cloud provider's agent to invoke.
            
            Analyze the user request, decide which cloud provider is used and respond with ONLY ONE of these words:
            - "aws" for Amazon Web Services (EC2, S3, Lambda, RDS, etc.)
            - "azure" for Microsoft Azure (VMs, Blob Storage, Functions, etc.)  
            - "gcp" for Google Cloud Platform (Compute Engine, Cloud Storage, etc.)
            
            If the request is not related to any cloud provider, respond with "unknown".
            
            User Input: {input}
            
            Response:"""
        )

        self.routing_chain = (
            self.router_prompt
            | self.model
            | StrOutputParser()
            | RunnableLambda(self._clean_destination)
        )

    def _clean_destination(self, destination: str) -> str:
        """Clean and validate the routing destination"""
        destination = destination.strip().lower()

        if "aws" in destination:
            return "aws"
        elif "azure" in destination:
            return "azure"
        elif "gcp" in destination or "google" in destination:
            return "gcp"
        else:
            return "unknown" 

    async def route_and_execute(self, user_input: str):
        """Route the user input to the appropriate agent and execute it."""
        
        try:
            destination = await self.routing_chain.ainvoke({"input": user_input})
            
            print(f"Routing to: {destination.upper()}")
            
            if destination == "aws":
                return await run_aws_agent(user_input)
            elif destination == "azure":
                return await run_azure_agent(user_input)
            elif destination == "gcp":
                return await run_gcp_agent(user_input)
            else:
                # Return error instead of defaulting
                error_msg = f"Unable to determine cloud provider for: '{user_input}'\n" \
                           f"Detected destination: '{destination}'\n" \
                           f"Please specify a cloud provider (AWS, Azure, or GCP) related terminology in your request."
                return type('Result', (), {'output': error_msg})()
                
        except Exception as e:
            error_msg = f"Routing error: {e}\n" \
                       f"Please try rephrasing your request with a clear cloud provider."
            return type('Result', (), {'output': error_msg})()