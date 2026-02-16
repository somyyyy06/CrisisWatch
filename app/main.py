from fastapi import FastAPI
import os

app = FastAPI()

@app.get("/")
def root():
    return {
        "status": "alive",
        "port": os.environ.get("PORT")
    }
