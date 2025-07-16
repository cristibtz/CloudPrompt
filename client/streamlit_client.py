import asyncio
import os, sys
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerSSE
from dotenv import load_dotenv
import logfire
import streamlit as st
from rich.console import Console
from shared import run_aws_agent

console = Console()

def main():
    st.title("AWS Assistant")
    user_input = st.text_input("Enter your prompt:")
    if st.button("Submit") and user_input:
        with st.spinner("Processing..."):
            output = asyncio.run(run_aws_agent(user_input))
        st.markdown("### Response")
        st.code(output)

def main():
    # Streamlit UI
    st.set_page_config(
        page_title="AWS Assistant",
        page_icon="☁️",
        layout="wide"
    )

    st.title("☁️ AWS Assistant")
    st.markdown("Manage your AWS resources with simple LLM prompts")

    # Sidebar with examples
    st.sidebar.header("💡 Example Commands")
    st.sidebar.markdown("""
    - List all EC2 instances
    - Create a t2.micro instance
    - Stop instance i-1234567890abcdef0
    - List S3 buckets
    - Create S3 bucket my-new-bucket
    """)

    # Main input
    user_input = st.text_area(
        "Enter your AWS command:",
        placeholder="e.g., List all EC2 instances in us-east-1",
        height=100
    )

    col1, col2 = st.columns([1, 4])

    with col1:
        submit_button = st.button("🚀 Execute", type="primary")

    with col2:
        clear_button = st.button("🗑️ Clear")

    if clear_button:
        st.rerun()

    if submit_button and user_input:
        with st.spinner("⏳ Processing your request..."):
            try:
                # Run the async function
                result = asyncio.run(run_aws_agent(user_input))
                
                st.success("✅ Command executed successfully!")
                
                # Display the result
                if isinstance(result, str):
                    st.markdown("### Result")
                    st.code(result, language="json")
                elif isinstance(result, dict):
                    st.markdown("### Result")
                    st.json(result)
                else:
                    st.error("❌ Unexpected result format. Please try again.")
                    
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    main()