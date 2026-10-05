CACHED_SECRET = None
from shared.usermodels import UserInDB
from shared import settings,Message,Embedding
from processor.processing_service import ProcessorUtils
from typing import List
import logging
from sqlmodel import select,cast
from pgvector.sqlalchemy import Vector

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




# Initialize the OpenAI client pointing to Google's base URL


async def answer_question_from_context_gemini(context:str, messagehistory:List[Message]):
    from openai import OpenAI
    client = OpenAI(
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        api_key=settings.GEMINI_API_KEY  # Use your Gemini API key here
    )
    messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an elite scientific research assistant. Your task is to answer "
                        "the user's question based strictly on the provided document summary.\n\n"
                        "Rules:\n"
                        "1. Rely ONLY on the clear facts directly mentioned in the summary text.\n"
                        "2. Do not assume, extrapolate, or bring in outside knowledge.\n"
                        "3. If the answer cannot be found in the summary, respond with: 'I cannot find the answer in the provided summary.'\n"
                        "4. Keep your answer concise and reference the section of the summary if applicable." 
                    )
                },
                {
                    "role": "user",
                    "content": f"--- START SUMMARY CONTEXT ---\n{context}\n--- END SUMMARY CONTEXT ---\n\n"
                }
            ]
    
    messages.append(messagehistory)
    logging.debug(messages)
    try:
        response = client.chat.completions.create(
            # Use the specific Gemini 2.0 Flash-Lite identifier
            model="gemini-3.5-flash-lite", 
            messages=messages,
            temperature=0.0  # Kept at 0.0 for deterministic factual answers
        )
        logging.info(response.choices[0].message)
        return response.choices[0].message
    except Exception as e:
        logging.error(f"Error retrieving LLM response: {e}")
        raise Exception("Error occured - could not get a response from LLM.")

async def generate_query(session, id: int, messagehistory:List[Message]):
    """
    Fetch the context for a given message history.
    This function retrieves the relevant context based on the provided message history.
    """
    try:
        user_messages = " ".join([msg.content for msg in messagehistory[:5] if msg.role == "user"])
        putil = ProcessorUtils()
        query_embedding = putil.encode(user_messages)
        print(query_embedding)
        ##VECTOR SEARCH
        query2 = select(Embedding).where(Embedding.article_id == id)\
                .order_by(Embedding.vector.l2_distance(cast(query_embedding, Vector)))\
                .limit(2)
        result = await session.exec(query2)
        relevant_docs = result.all()

        context = "\n\n Retrieved portions of the paper:\n\n"
        for doc in relevant_docs:
            print(f"Found context match: {doc.chunk_text}")
            context += f"{doc.chunk_text}\n\n"
        return context
    except Exception as e:
        logging.error(f"Error generating query context: {e}")
        raise Exception("Error occurred while generating query context.")
    return ""