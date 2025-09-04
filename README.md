<h1 align="center">
 <a href="#">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="photos/logo.png"/>
    <img height="240" width="240" src="photos/logo.png"/>
  </picture>
 </a>
 <br />
</h1>
<p align="center">
    ☁️ Automate cloud infrastructure tasks using simple LLM prompts ☁️
</p>

![Animation](photos/Animation.gif)

## Setup .env file in root directory
```.env
#AWS Credentials
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=

#Proxmox Credentials
PROXMOX_HOST=
PROXMOX_USER=
PROXMOX_PASS=

#OPENAI Configs
MODEL=gpt-4o-mini
OPENAI_API_KEY=

#Logfire token
LOGFIRE_TOKEN=

```
## Setup .env file in backend directory
```.env
DB_USERNAME=cloudprompt
DB_PASSWORD=cloudprompt
DB_HOST=
DB_NAME=cloudprompt

KEYCLOAK_SERVER_URL=
KEYCLOAK_REALM=cloudprompt
KEYCLOAK_CLIENT_ID=cloudprompt-client
WEBHOOK_SECRET=cloudprompt-secret
KEYCLOAK_ADMIN_USERNAME=cloudprompt-admin
KEYCLOAK_ADMIN_PASSWORD=cloudprompt

ENCRYPTION_KEY=
```

## Setup .env file in frontend directory
```.env
VITE_API_BASE_URL=
VITE_APP_NAME=CloudPrompt
VITE_APP_VERSION=0.0.2

VITE_KEYCLOAK_URL=http://192.168.100.11:8080
VITE_KEYCLOAK_REALM=cloudprompt
VITE_KEYCLOAK_CLIENT_ID=cloudprompt-client
```

## Development Setup
1. Clone the repository:
    ```bash
    git clone https://github.com/cristibtz/CloudPrompt.git
    cd CloudPrompt
    ```
2. Setup virtual environment and install the required packages:
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows use 'venv\Scripts\activate'
    pip install -e .
    ```
3. Set up the `.env` file with your credentials and configurations as shown above.
4. Start MCP server:
    ```bash
    cd mcp_server/
    pip install -r requirements.txt
    python3 server.py
    ```
5. Start backend API:
    ```bash
    cd backend/
    pip install -r requirements.txt
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8888
    ```
6. Start frontend:
    ```bash
    cd cloudprompt-frontend
    npm install
    npm run dev
    ```
7. Open your browser and navigate to `http://localhost:5173` to access the CloudPrompt frontend. Or use CLI tool:
    ```bash
    cloudprompt -p 'PROMPT' -c 'CLOUD PROVIDER
    ```

## CLI Client Usage
```bash
cloudprompt -p "List ec2 instances" -c "aws"
```

## Crypto Key
```Generate encryption key
python3 -c "import secrets; print(secrets.token_hex(32))"
```