from fastapi import FastAPI
from api.v1.router import v1_router
from sqlmodel import SQLModel
from shared import settings
from mangum import Mangum
import os

STAGE = settings.STAGE_NAME 


app = FastAPI(
    title="Research Watcher API",
    root_path=f"/{STAGE}" if STAGE else None
)

handler = Mangum(app)


CACHED_SECRET = None

def get_secret_runtime():
    import boto3
    from botocore.exceptions import ClientError
    global CACHED_SECRET
    
    # If we already fetched it during cold start or a previous run, reuse it instantly
    if CACHED_SECRET is not None:
        return CACHED_SECRET

    secret_name = "your-staging-secret-name"
    region_name = "us-east-1"  # Replace with your AWS region

    # Initialize the boto3 Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name="secretsmanager",
        region_name=region_name
    )

    try:
        print("Fetching secret from AWS Secrets Manager...")
        response = client.get_secret_value(SecretId=secret_name)
        
        # Secrets Manager stores secrets as either a string or binary
        if "SecretString" in response:
            secret = response["SecretString"]
        else:
            import base64
            secret = base64.b64decode(response["SecretBinary"]).decode("utf-8")
            
        # Parse JSON strings into a Python dict if your secret contains key-value pairs
        try:
            CACHED_SECRET = json.loads(secret)
        except json.JSONDecodeError:
            CACHED_SECRET = secret
            
        return CACHED_SECRET

    except ClientError as e:
        print(f"Error retrieving secret: {e.response['Error']['Message']}")
        raise e
    

@app.on_event("startup")
async def on_startup():
    print(f"Registered tables: {SQLModel.metadata.tables.keys()}")
    #TODO:Get secret from secret manager


app.include_router(v1_router)