from shared import get_session
from shared import Article,RelevanceScore,Keyword
from sqlmodel import select
from contextlib import asynccontextmanager
import logging
from typing import List

async def removeDuplicates(session, IDList:List[str]):
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
            session.add(currArticle)  # Add the object to the session
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
        statement = (
            select(Article)
            .where(Article.processed == False)
            .with_for_update(skip_locked=True)
            .limit(limit)
        )
        result = await session.exec(statement)
        curr_batch = result.all()
        return curr_batch
    except Exception as e:
        logging.error(f"Error occurred: {e}")
        logging.exception(e)
    return curr_batch


async def saveRelevanceScore(session,score:RelevanceScore)->RelevanceScore:
    if RelevanceScore.model_validate(score):
        try:
            session.add(score)
            await session.commit()     # Save it to the database
            await session.refresh(score) # Refresh to get the generated ID from the DB
            return score
        except Exception as e:
            logging.error(f"Error in saving score for article ID{score.article_id} - {e}")
             

async def saveKeywords(session,keywords:List[str],article:Article):
    try:
        for item in keywords:
            key = Keyword(article_id=article.id,word=item)
            key = Keyword.model_validate(key)
            session.add(key)
            #await session.refresh(key) # Refresh to get the generated ID from the DB

        await session.commit()    
    except Exception as e:
        logging.error(f"Error in saving keywords for article {article.arxiv_id} - {e}")
        session.rollback()
    finally:
        session.close()
    

          