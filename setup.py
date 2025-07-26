from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements from requirements.txt if it exists
try:
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]
except FileNotFoundError:
    requirements = [
        "boto3",
        "openai",
        "rich",
        "python-dotenv",
        "fastapi",
        "uvicorn",
        "logfire",
        "mcp",
        "starlette",
    ]

setup(
    name="cloudprompt",
    version="0.0.1",
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