CACHED_SECRET = None
from shared.usermodels import UserInDB
import logging

from shared import get_session
def get_secret_runtime():
    import boto3
    from botocore.exceptions import ClientError
    global CACHED_SECRET
    
    # If we already fetched it during cold start or a previous run, reuse it instantly
    if CACHED_SECRET is not None:
        return CACHED_SECRET

    secret_name = "rds!db-6c4a6398-7b05-4750-b0ff-395702773b38"
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
    
async def create_default_user():
    async with get_session() as session:
        try:
            
            user = UserInDB(username="johndoe",
                            email="johndoe@example.com",
                            full_name="John Doe",
                            disabled=False,
                            hashed_password="$argon2id$v=19$m=65536,t=3,p=4$wagCPXjifgvUFBzq4hqe3w$CYaIb8sB+wtD+Vu/P4uod1+Qof8h+1g7bbDlBID48Rc")

            session.add(user)
            await session.commit()
        except Exception as e:
            print("User creation failed")
            logging.exception(e)
            pass
