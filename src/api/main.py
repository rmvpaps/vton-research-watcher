from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from api.v1.router import v1_router
from sqlmodel import SQLModel
from shared import settings
from mangum import Mangum
import logging
from api.utils import create_default_user

STAGE = settings.STAGE_NAME 
logger = logging.getLogger("ArxivWatcherAPI")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

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
    if settings.defaultuser == 1:
        try:
            await create_default_user()
        except Exception as e:
            logging.error(f"Default user creation failed {e}")

app.include_router(v1_router)