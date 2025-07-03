from fastapi import FastAPI
from pydantic import BaseModel
import numpy as np
from ..extractor import extract
from ..model.cosine_kernel import CosineKernel

app = FastAPI(title="Linker Scaffold API")
kernel = CosineKernel()

class Query(BaseModel):
    text: str

@app.get("/ping")
def ping(): return {"pong": True}

@app.post("/link")
def link(q: Query):
    tuples = extract(q.text)
    vec = np.ones(16)  # placeholder fixed vector
    score = kernel.forward(vec, vec)
    return {"edges": [{"src": q.text, "dst": "dummy", "score": score, "tuples": tuples}]}