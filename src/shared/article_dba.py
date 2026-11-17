from shared.database import get_session
from shared.models import Article,RelevanceScore,Keyword, Embedding,Enriched
from sqlmodel import select
from contextlib import asynccontextmanager
import logging
from typing import List

logger = logging.getLogger(__name__)

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
        logger.error(f"Error occurred: {e}")
        logger.exception(e)
    return new_ids

async def store_results(session,currArticle:Article)->Article:
        logger.info("Storing fetched abstract and writing to queue")

        try:
            session.add(currArticle)  # Add the object to the session
            await session.commit()     # Save it to the database
            await session.refresh(currArticle) # Refresh to get the generated ID from the DB
            logger.info(f"Inserted article with id {currArticle.id}")
            return currArticle
        except Exception as e:
            logger.exception(e)
            logger.error(f"Error in saving article raw {e}")


async def updateArticle(session,currArticle:Article)->Article:
        logger.info("Storing fetched abstract and writing to queue")

        try:
            session.add(currArticle)  # Add the object to the session
            await session.commit()     # Save it to the database
            await session.refresh(currArticle) # Refresh to get the generated ID from the DB
            logger.info(f"updated article with id {currArticle.id}")
            return currArticle
        except Exception as e:
            logger.exception(e)
            logger.error(f"Error in saving article raw {e}")

async def fetch_next_batch(session, limit:int):
    curr_batch=[]
    try:
        statement = (
            select(Article)
            .where(Article.processed == False)
            .order_by(Article.fetched_at.desc())
            .with_for_update(skip_locked=True)
            .limit(limit)
        )
        result = await session.exec(statement)
        curr_batch = result.all()
        return curr_batch
    except Exception as e:
        logger.error(f"Error occurred: {e}")
        logger.exception(e)
    return curr_batch


async def saveRelevanceScore(session,score:RelevanceScore)->RelevanceScore:
    if RelevanceScore.model_validate(score):
        try:
            session.add(score)
            await session.commit()     # Save it to the database
            await session.refresh(score) # Refresh to get the generated ID from the DB
            return score
        except Exception as e:
            logger.error(f"Error in saving score for article ID{score.article_id} - {e}")
             

async def saveKeywords(session,keywords:List[str],article:Article):
    try:
        for item in keywords:
            key = Keyword(article_id=article.id,word=item)
            key = Keyword.model_validate(key)
            session.add(key)
            #await session.refresh(key) # Refresh to get the generated ID from the DB

        await session.commit()    
    except Exception as e:
        logger.error(f"Error in saving keywords for article {article.arxiv_id} - {e}")
        await session.rollback()
    finally:
        await session.close()
    

async def saveEmbeddings(session,enriched:Enriched, vectors:List[List[float]]):
    try:
        for idx, chunk in enumerate(enriched.chunks):
            embedding = Embedding(
                article_id=enriched.id,
                chunk_id=idx,
                chunk_text=chunk,
                vector=vectors[idx]
            )
            session.add(embedding)

        await session.commit()    
    except Exception as e:
        logger.error(f"Error in saving embeddings for article {enriched.arxiv_id} - {e}")
        await session.rollback()
    finally:
        await session.close()
