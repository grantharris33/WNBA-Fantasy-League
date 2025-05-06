from fastapi import FastAPI
import uvicorn

from app.core.database import init_db

from app.api import router as api_router

init_db()

app = FastAPI()

app.include_router(api_router)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
