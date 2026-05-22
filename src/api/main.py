from fastapi import FastAPI
from api.v1.router import v1_router
from sqlmodel import SQLModel
from shared import settings
from mangum import Mangum
import os
from api.utils import create_default_user

STAGE = settings.STAGE_NAME 


app = FastAPI(
    title="Research Watcher API",
    root_path=f"/{STAGE}" if STAGE else None
)

handler = Mangum(app)




@app.on_event("startup")
async def on_startup():
    print(f"Registered tables: {SQLModel.metadata.tables.keys()}")
    #TODO:Get secret from secret manager

    #CREATE DEFAULT USER
    #await create_default_user()


app.include_router(v1_router)