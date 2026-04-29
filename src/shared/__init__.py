from shared.models import ArticleBase, Article,RelevanceScore,Enriched,Keyword,BGEEmbedding
from shared.config import settings
from shared.database import get_session,create_tables,delete_database,create_database
from shared.article_dba import fetch_next_batch,updateArticle,saveKeywords,saveRelevanceScore
#from shared.messagebroker import messageq