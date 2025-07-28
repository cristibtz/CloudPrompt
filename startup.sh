#!/bin/bash

# Check if virtual environment exists
if [ ! -d "./venv" ]; then
    echo "Virtual environment not found. Please create it first."
    exit 1
fi

# Start MCP server
echo "Starting MCP server..."
./venv/bin/python3 mcp_server/mcp_server.py &> /dev/null &
MCP_PID=$!
echo "MCP server started"

echo ""
echo "Starting CloudPrompt environment..."
echo "Virtual environment will be activated in a new shell."
echo "Type 'exit' to leave CloudPrompt environment."
echo ""

# Start a new shell with venv activated
exec bash --rcfile <(echo "source ./venv/bin/activate; echo 'CloudPrompt environment ready! Test with: cloudprompt -p \"List my EC2 instances\"'")