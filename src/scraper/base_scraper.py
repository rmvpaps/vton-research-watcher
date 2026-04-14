from abc import ABC, abstractmethod
from typing import List
from shared.models import ArticleBase # Your Pydantic model
import httpx


class BaseScraper(ABC):

    @abstractmethod
    async def fetch_ids(self, client:httpx.AsyncClient, limit: int) -> List[str]:
        """Fetch a list of paper IDs from the source."""
        pass

    @abstractmethod
    async def fetchPaperDetails(self,client:httpx.AsyncClient, id:str)->ArticleBase:
        """Fetch and parse specific paper details."""
        pass

    @abstractmethod
    async def get_details_batch(self, client: httpx.AsyncClient, id_list: List[str]) -> List[ArticleBase]:
        """Fetch paper details as a batch task"""
        pass
    



