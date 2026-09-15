from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from api.v1.router import v1_router
from sqlmodel import SQLModel
from shared import settings
from mangum import Mangum
import logging
from api.utils import create_default_user,get_secret_runtime
from fastapi.middleware.cors import CORSMiddleware
STAGE = settings.STAGE_NAME 
logger = logging.getLogger("ArxivWatcherAPI")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
from fastapi.openapi.utils import get_openapi

app = FastAPI(
    title="Research Watcher API",
    root_path=f"/{STAGE}" if STAGE else None
)

handler = Mangum(app)




# 🔒 Configure CORS Origins
origins = [ settings.FRONTEND_ORIGIN]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allows GET, POST, OPTIONS, etc.
    allow_headers=["*"],  # Allows Authorization, Content-Type, etc.
)


@app.on_event("startup")
async def on_startup():
    print(f"Registered tables: {SQLModel.metadata.tables.keys()}")
    #Get secret from secret manager
    if settings.STAGE_NAME != "" and settings.POSTGRES_PASSWORD == "default123":
        try:
            settings.POSTGRES_PASSWORD = get_secret_runtime()
        except Exception as e:
            logging.error(f"Error in fetching secret {e}")
            raise Exception(f"DB Passoword not loaded from SecretManager")
        
    #CREATE DEFAULT USER
    if settings.defaultuser == 1:
        try:
            await create_default_user()
        except Exception as e:
            logging.error(f"Default user creation failed {e}")


app.include_router(v1_router)