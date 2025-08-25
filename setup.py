from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements from requirements.txt if it exists
try:
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]
except FileNotFoundError:
    requirements = [
        "boto3==1.39.14",
        "botocore==1.39.14",
        "dotenv==0.9.9",
        "logfire==4.0.0",
        "logfire[langchain]==4.0.0",
        "fastmcp==2.10.6",
        "httpx==0.28.1",
        "pydantic_ai==0.4.5",
        "streamlit==1.47.1",
        "rich==14.1.0",
        "langchain==0.3.27",
        "langchain_community==0.3.27",
        "langchain_openai==0.3.28",
        "proxmoxer==2.2.0",
    ]

setup(
    name="cloudprompt",
    version="0.0.2",
    author="Cristian Branet",
    author_email="branet.cristian@gmail.com",
    description="Automate cloud infrastructure tasks using simple LLM prompts",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/cristibtz/LLMCloud",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "cloudprompt=cloudprompt.cli.cli_client:main_sync",
        ],
    },
    include_package_data=True,
)