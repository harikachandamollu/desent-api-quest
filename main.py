from fastapi import FastAPI, Body
from typing import Any

app = FastAPI(title="Desent API Quest")

@app.get("/ping")
def ping():
    return {"success": "True"}

@app.post("/echo")
def echo(payload: Any = Body(...)):
    return payload

