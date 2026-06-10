from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from api.v1.router import v1_router
from sqlmodel import SQLModel
from shared import settings
from mangum import Mangum
import logging
from api.utils import create_default_user
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
    #TODO:Get secret from secret manager

    #CREATE DEFAULT USER
    if settings.defaultuser == 1:
        try:
            await create_default_user()
        except Exception as e:
            logging.error(f"Default user creation failed {e}")

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Research Librarian API",
        version="1.0.0",
        openapi_version="3.0.3", # Enforce version 3.0
        routes=app.routes,
    )
    
    # 🟢 FIX FOR BEDROCK: Clean up 3.1 type arrays in the components schemas
    components = openapi_schema.get("components", {})
    schemas = components.get("schemas", {})
    
    for schema_name, schema in schemas.items():
        properties = schema.get("properties", {})
        for prop_name, prop in properties.items():
            # If FastAPI generated a 3.1 type list e.g., ["string", "null"]
            if isinstance(prop.get("type"), list):
                type_list = prop["type"]
                if "null" in type_list:
                    # Filter out 'null' to get the primary type (e.g., 'string' or 'integer')
                    remaining_types = [t for t in type_list if t != "null"]
                    if remaining_types:
                        prop["type"] = remaining_types[0] # Set to primary type
                    prop["nullable"] = True # 🟢 Re-add the 3.0 nullable flag

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

app.include_router(v1_router)