import os
from dotenv import load_dotenv

load_dotenv()

import logfire
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda
from cloudprompt.agent.agent import run_aws_agent, run_azure_agent, run_gcp_agent, run_proxmox_agent

logfire.configure(
    token=os.getenv("LOGFIRE_TOKEN")
    )

class CloudRouterAgent:
    def __init__(self):
        logfire.info("Initializing CloudRouterAgent")
        
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
            - "proxmox" for Proxmox
            
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
        elif "proxmox" in destination:
            return "proxmox"
        else:
            return "unknown"

    async def route_and_execute(self, user_input: str):
        """Route the user input to the appropriate agent and execute it."""
        
        with logfire.span('cloud_router.route_and_execute', user_input=user_input) as span:
            try:
                logfire.info("Router: Processing request", user_input=user_input)
                
                with logfire.span('cloud_router.routing_decision'):
                    destination = await self.routing_chain.ainvoke({"input": user_input})
                
                logfire.info("Router: Decision made", destination=destination, user_input=user_input)
                span.set_attribute("destination", destination)
                print(f"Routing to: {destination.upper()}")
                
                if destination == "aws":
                    with logfire.span('cloud_router.execute_aws_agent'):
                        return await run_aws_agent(user_input)
                elif destination == "azure":
                    with logfire.span('cloud_router.execute_azure_agent'):
                        return await run_azure_agent(user_input)
                elif destination == "gcp":
                    with logfire.span('cloud_router.execute_gcp_agent'):
                        return await run_gcp_agent(user_input)
                elif destination == "proxmox":
                    with logfire.span('cloud_router.execute_proxmox_agent'):
                        return await run_proxmox_agent(user_input)
                else:
                    logfire.warn("Router: Unknown destination", destination=destination)
                    span.set_attribute("error", "unknown_destination")
                    error_msg = f"Unable to determine cloud provider for: '{user_input}'\n" \
                               f"Detected destination: '{destination}'\n" \
                               f"Please specify a cloud provider (AWS, Azure, or GCP) related terminology in your request."
                    return type('Result', (), {'output': error_msg})()
                    
            except Exception as e:
                logfire.error("Router: Execution failed", error=str(e), user_input=user_input)
                span.record_exception(e)
                span.set_attribute("error", True)
                error_msg = f"Routing error: {e}\n"
                return type('Result', (), {'output': error_msg})()