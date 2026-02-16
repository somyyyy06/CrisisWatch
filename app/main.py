from fastapi import FastAPI
import os
import sys

print("Python version:", sys.version)
print("PORT:", os.environ.get("PORT"))

app = FastAPI()

@app.get("/")
def root():
    return {"status": "ok"}

@app.get("/health")
def health():
    return {"status": "healthy"}
