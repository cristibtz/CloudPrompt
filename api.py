from fastapi import FastAPI, Form
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/execute")
async def execute_prompt(prompt: str = Form(...)):
    return {"prompt": prompt}