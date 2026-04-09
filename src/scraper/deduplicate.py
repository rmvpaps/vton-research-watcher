from shared import get_session
from shared import Article
from sqlmodel import select

import logging

async def removeDuplicates(IDList:list[str]):
    new_ids=[]
    try:
        async with get_session() as session:
            statement = select(Article.arxiv_id).where(Article.arxiv_id.in_(IDList))
            result = await session.exec(statement)
            existing_ids = result.all()
            print(existing_ids)
            existing_set = set(existing_ids)
            new_ids = [id for id in IDList if id not in existing_set]
            return new_ids
    except Exception as e:
        logging.error(f"Error occurred: {e}")
        logging.exception(e)
    return new_ids