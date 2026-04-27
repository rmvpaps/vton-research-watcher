from abc import ABC, abstractmethod
from typing import List
from shared.models import Article,RelevanceScore # Your Pydantic model


class BaseProcessor(ABC):

    @abstractmethod
    async def evaluate_abstract(self, article:Article)->RelevanceScore:
        """Match against keyword list and generate score"""
        pass

    @abstractmethod
    async def evaluate_text(self, article:Article)->Article:
        """Generate a summary, keep the summary vector, generate keywords from fullText"""
        pass

    @abstractmethod
    async def generateSummary(self, article:Article, actualText:str)->str:
        """Generate Summary from abstract and title and actual text and update Article in-place"""
        pass

    @abstractmethod
    async def generateKeywords(self, article:Article, actualText:str)->List[str]:
        """Generate Keywords from abstract,title and actual text and return the list"""
        pass
    


