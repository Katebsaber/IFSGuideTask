from llama_cpp import Llama
from config import MODEL_PATH
from fastapi import FastAPI, Request

# Load the model
llm = Llama(model_path=MODEL_PATH)

app = FastAPI()

@app.get("/api/v1/agent")
async def llama(request: Request, prompt:str):
    stream = llm(
        f"""{prompt}""",
        max_tokens=100,
        stop=["\n", "\n\n", " Q:", "human:"],
        stream=False,
    )
    if len(stream["choices"]) > 0: 
        message = stream["choices"][0]["text"]

        return message
    else:
        return {}
