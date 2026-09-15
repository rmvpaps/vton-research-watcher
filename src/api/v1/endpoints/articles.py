from typing import Annotated
from shared import get_session_dep,Article,settings,RelevanceScore,Enriched,ArticleState,Keyword,Stats,Message
from fastapi import Depends, FastAPI, HTTPException, Query, APIRouter,Path
from sqlmodel import Field, Session, SQLModel, create_engine, select,desc,func
from typing import List,Optional
from api import get_current_user
from api.utils import answer_question_from_context_gemini
from shared.usermodels import User
from typing import Annotated
router = APIRouter()
SessionDep = Annotated[Session, Depends(get_session_dep)]
import datetime



@router.get("",response_model=List[Enriched])
async def read_articles(
    session: SessionDep,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    processed: Optional[bool] = None,
    state: Optional[ArticleState] = None,
    sort_by_score: bool = False,
    ids: Optional[List[int]] = Query(None) 
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
    if ids and len(ids)>0:
        query = query.where(Article.id.in_(ids))
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



@router.get("/keywords",response_model=List[str])
async def get_keywords_for_article(
    session: SessionDep,
    id: int = Query(None)  
) -> List[str]:
    """
    Retrieves the keywords for given article
    """
    query = select(Keyword.word).where(Keyword.article_id == id)
    results = await session.exec(query)
    response_data = results.all()

    return response_data


@router.post("/chat/{id}",response_model=Message)
async def get_answer_from_article(
    session: SessionDep,
    messages: List[Message],  # FastAPI automatically treats this as the JSON Request Body
    id: int = Path(..., description="The ID of the article to chat with")
   
) -> Message:
    """
    Retrieves the chat response for a question based on given article and message history
    """
    query = select(Article.title,Article.abstract, Article.summary).where(Article.status == "indexed").where(Article.id  == id)
        
    results = await session.exec(query)
    response_data = results.one()

    context = f"{response_data.title}\n\n{response_data.abstract}\n\n{response_data.summary}"

    llm_response = await answer_question_from_context_gemini(context,messages)

    return llm_response


@router.get("/stats",response_model=Stats)
async def get_system_stats(
    session: SessionDep 
) -> Stats:
    """
    Retrieves the daily, monthly, total relevant, total parsed abstracts
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    start_of_day = datetime.datetime(now.year, now.month, now.day)
    start_of_month = datetime.datetime(now.year, now.month, 1)

    # 1. Articles scraped today
    stmt_d = select(func.count(Article.id)).where(Article.scraped_at >= start_of_day)
    res_d = await session.exec(stmt_d)
    day_ct = res_d.one()

    # 2. Articles scraped this month
    stmt_m = select(func.count(Article.id)).where(Article.scraped_at >= start_of_month)
    res_m = await session.exec(stmt_m)
    month_ct = res_m.one()

    # 3. Total relevant/indexed articles
    stmt_r = select(func.count(Article.id)).where(Article.status == ArticleState.INDEXED)
    res_r = await session.exec(stmt_r)
    total_rel_ct = res_r.one()

    # 4. Total overall articles
    stmt_t = select(func.count(Article.id))
    res_t = await session.exec(stmt_t)
    total_ct = res_t.one()

    return Stats(
        dayCt=day_ct,
        monthCt=month_ct,
        totalRelCt=total_rel_ct,
        totalCt=total_ct,
    )


@router.get("/recent",response_model=List[Article])
async def get_recent_articles(
    session: SessionDep 
) -> List[Article]:
    """
    Retrieves a list of all research article abstracts and keywords published 
    within the last 7 days. Use this tool first when a user asks for recent research.
    """
    dt7days = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=27)
    # 3. Pagination
    query = select(Article.id,Article.abstract,Article.title,Article.arxiv_id,Article.status,Article.processed).where(Article.status == "indexed").where(Article.fetched_at >= dt7days)
    
    # 4. Execute Query
    results = await session.exec(query)

    #Transform the results -  since we have cap of 100, we can loop without performance hit
    response_data = results.all()

    return response_data


# --- 2. KEYWORD EXACT MATCH SEARCH ---
@router.get("/search/keyword", response_model=List[Enriched])
async def search_articles_by_keyword(
    session: SessionDep,
    current_user: Annotated[User, Depends(get_current_user)],
    q: str = Query(..., min_length=1, description="The keyword or tag to search for"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort_by_score: bool = False,
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
