from fastapi import FastAPI
from api.v1.router import v1_router
from sqlmodel import SQLModel
from shared import settings
app = FastAPI()

@app.on_event("startup")
async def on_startup():
    print(f"Registered tables: {SQLModel.metadata.tables.keys()}")
    print(settings.database_url)


app.include_router(v1_router)