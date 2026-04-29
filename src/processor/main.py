import os
# MUST be set before any 'transformers' related imports
os.environ['TRANSFORMERS_OFFLINE'] = '1'
os.environ['HF_DATASETS_OFFLINE'] = '1' # Good practice to include this too

import asyncio
import logging
from processor import ProcessingService

logger = logging.getLogger("ArxivData Processor")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

async def main():

    
    service = ProcessingService()
    await  service.fetch_next_batch_and_process()


if __name__ == "__main__":
    asyncio.run(main())
