from shared import get_session
from shared import Article
from sqlmodel import select
from contextlib import asynccontextmanager
import logging

async def removeDuplicates(session, IDList:list[str]):
    new_ids=[]
    try:
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

async def store_results(session,currArticle:Article)->Article:
        logging.info("Storing fetched abstract and writing to queue")

        try:
            session.add(currArticle)  # Add the object to the session
            await session.commit()     # Save it to the database
            await session.refresh(currArticle) # Refresh to get the generated ID from the DB
            logging.info(f"Inserted article with id {currArticle.id}")
            return currArticle
        except Exception as e:
            logging.exception(e)
            logging.error(f"Error in saving article raw {e}")


async def updateArticle(session,currArticle:Article)->Article:
        logging.info("Storing fetched abstract and writing to queue")

        try:
            session.save(currArticle)  # Add the object to the session
            await session.commit()     # Save it to the database
            await session.refresh(currArticle) # Refresh to get the generated ID from the DB
            logging.info(f"updated article with id {currArticle.id}")
            return currArticle
        except Exception as e:
            logging.exception(e)
            logging.error(f"Error in saving article raw {e}")

async def fetch_next_batch(session, limit:int):
    curr_batch=[]
    try:
        statement = select(Article).limit(limit)
        result = await session.exec(statement)
        curr_batch = result.all()
        return curr_batch
    except Exception as e:
        logging.error(f"Error occurred: {e}")
        logging.exception(e)
    return curr_batch
