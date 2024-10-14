from .routers import Router
from fastapi import FastAPI
from typing import Dict
import uvicorn
import logging


logger = logging.getLogger("uvicorn")
logger.setLevel(logging.INFO)

app = FastAPI()
app.include_router(Router.router)


@app.get("/")
def ping() -> Dict:
    return {"status": "working"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
