import os
# MUST be set before any 'transformers' related imports
os.environ['TRANSFORMERS_OFFLINE'] = '1'
os.environ['HF_DATASETS_OFFLINE'] = '1' # Good practice to include this too

import asyncio
import logging
from processor import ProcessingService

logger = logging.getLogger("ArxivData Processor")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
import os

async def main():
    path = "/app/models/bge-small"
    print(f"Checking path: {path}")
    if os.path.exists(path):
        print(f"Directory exists! Contents: {os.listdir(path)}")
    else:
        print(f"DIRECTORY MISSING. Current workdir ({os.getcwd()}) contents: {os.listdir('.')}")
        raise Exception("Missing models")
    
    service = ProcessingService()
    await  service.fetch_next_batch_and_process()


if __name__ == "__main__":
    asyncio.run(main())
