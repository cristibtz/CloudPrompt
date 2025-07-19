# LLMCloud
Automate cloud infrastructure tasks using simple LLM prompts


## Setup .env file
```.env
#AWS Credentials
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=

#OPENAI Configs
MODEL=gpt-4o-mini
OPENAI_API_KEY=

#Logfire token
LOGFIRE_TOKEN=
```

## To do

- [x] Read AWS boto3 docs for EC2 and S3
    - [x] EC2
    - [x] S3
- [x] Document each MCP server tool
- [ ] Improve app's codebase structure
    - [ ] Redo app's architecture in draw.io
    - [x] Define folder corresponding to app's architecture (frontend, backend, MCP server, etc)
    - [ ] Classify code accordingly to its appearance frequency and its functions
- [ ] Improve:
    - [ ] Add try/catch blocks wherever suited
    - [ ] Backend
    - [ ] CLI tool
    - [ ] MCP server
- [ ] Create frontend prototype
- [ ] Learn about API usage costs
    - [ ] Cost debugging
    - [ ] Cost monitoring and logging

