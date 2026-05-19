from typing import Annotated
from shared import get_session_dep,Article,settings,RelevanceScore,Enriched,ArticleState,Keyword
from fastapi import Depends, FastAPI, HTTPException, Query, APIRouter
from sqlmodel import Field, Session, SQLModel, create_engine, select,desc
from typing import List,Optional
import asyncio
router = APIRouter()
SessionDep = Annotated[Session, Depends(get_session_dep)]




@router.get("",response_model=List[Enriched])
async def read_articles(
    session: SessionDep,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    processed: Optional[bool] = None,
    state: Optional[ArticleState] = None,
    sort_by_score: bool = False  
) -> List[Enriched]:
    """Returns all articles in the system"""
    query = select(Article, RelevanceScore).join(
        RelevanceScore, Article.id == RelevanceScore.article_id,isouter=True
    )
    if sort_by_score:
        query = query.order_by(desc(RelevanceScore.score))
    else:
        query = query.order_by(desc(Article.id))

    # 2. Apply Optional Metadata Filters
    if processed is not None:
        query = query.where(Article.processed == processed)
    if state is not None:
        query = query.where(Article.status == state)

    # 3. Pagination
    query = query.offset(offset).limit(limit)
    
    # 4. Execute Query
    results = await session.exec(query)

    #Transform the results -  since we have cap of 100, we can loop without performance hit
    response_data = []
    for row in results.all():
        article_obj, score_obj = row

        if score_obj:    
            # Merge fields into our flat Pydantic/SQLModel response structure
            response_data.append(
                Enriched(**article_obj.model_dump(),score=score_obj.score)
            )
        else:
            response_data.append(
                Enriched(**article_obj.model_dump())
            )
    return response_data



# --- 2. KEYWORD EXACT MATCH SEARCH ---
@router.get("/search/keyword", response_model=List[Enriched])
async def search_articles_by_keyword(
    session: SessionDep,
    q: str = Query(..., min_length=1, description="The keyword or tag to search for"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort_by_score: bool = False
):
    """
    Joins with the keywords table to find articles explicitly tagged
    or containing the specified text string.
    """
    search_term = f"%{q}%"
    keyword_subquery = (
        select(Keyword.article_id)
        .where(Keyword.word.ilike(search_term))
    ).subquery()

    # 2. Base query on the main Article table, filtering where ID is in our subquery
    query = select(Article,RelevanceScore).where(Article.id.in_(select(keyword_subquery)))
    
    
    query = query.join(RelevanceScore,Article.id == RelevanceScore.article_id)
    
    if sort_by_score:
        query = query.order_by(desc(RelevanceScore.score))
    else:
        query = query.order_by(desc(Article.id))

    # 3. Pagination
    query = query.offset(offset).limit(limit)
    
    # 4. Execute Query
    results = await session.exec(query)

    #Transform the results -  since we have cap of 100, we can loop without performance hit
    response_data = []
    for row in results.all():
        article_obj, score_obj = row

        if score_obj:    
            # Merge fields into our flat Pydantic/SQLModel response structure
            response_data.append(
                Enriched(**article_obj.model_dump(),score=score_obj.score)
            )
        else:
            response_data.append(
                Enriched(**article_obj.model_dump())
            )
    return response_data
