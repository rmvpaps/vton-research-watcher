"""
Project to learn asyncio in python 3.1x by 
 - scraping arXiv for new entries in computer vision    
 - find keywords and summary of abstract and title
 - check for keywords like Virtual Try on, human parametric model, 3D reconstruction
 - enter into results.md if relevant
"""

import asyncio
import httpx

from bs4 import BeautifulSoup
import logging
import time
import aiofiles
from shared import Article,get_session,settings
from typing import List
from scraper.base_scraper import BaseScraper

baseURL = "https://arxiv.org/list/cs.CV/pastweek?skip=0&show=25"
CONCURRENCY_LIMIT = settings.scrape_concurrency
ARXIV_ABS_URL = "https://arxiv.org/abs/"




class HtmlScraper(BaseScraper):
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.curr_num = 0
        self.semaphore = asyncio.Semaphore(settings.scrape_concurrency)


            
    def extract_ids(self,html_content:str) -> List[str]:
        # Parse HTML content with BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')

        # Find all dl tags containing dt tags
        dl_tags = soup.find_all('dl')

        # List to store extracted IDs
        extracted_ids = []

        # Iterate through dl tags
        for dl_tag in dl_tags:
            # Find all dt tags within the current dl tag
            dt_tags = dl_tag.find_all('dt')

            # Iterate through dt tags
            for dt_tag in dt_tags:
            
                # Find the a tag within the span tag
                a_tag = dt_tag.find('a',attrs={'title':'Abstract'})

                # Check if the a tag has a title containing "Abstract"
                if a_tag and a_tag.get('title', '').lower() == 'abstract':
                    # Extract the 'href' attribute, which contains the ID
                    href_attr = a_tag.get('href')

                    # Extract the ID from the 'href' attribute
                    id_value = href_attr.split('/')[-1]

                    # Append the ID to the list
                    extracted_ids.append(id_value)

        return extracted_ids
    
    async def get_details_batch(self, client: httpx.AsyncClient, id_list: List[str]) -> List[Article]:
        """
        Implementation of the batch fetch using TaskGroup.
        """
        logging.info(f"Starting batch fetch for {len(id_list)} IDs")
        tasks = []
        
        try:
            async with asyncio.TaskGroup() as tg:
                if settings.dummy:
                    id_list = id_list[0:3]
                for article_id in id_list:
                    # We create and store task references to collect results later
                    task = tg.create_task(self.fetchPaperDetails(client, article_id))
                    tasks.append(task)
        except ExceptionGroup as eg:
            logging.error(f"Batch processing encountered errors: {eg}")

        # Collect results from tasks that succeeded
        results = [t.result() for t in tasks if not t.cancelled() and t.result() is not None]
        return results

    async def fetchPaperDetails(self,client:httpx.AsyncClient, id:str)->Article:
        async with self.semaphore:
            print("Fetch individual abstract")
            try:
                url = ARXIV_ABS_URL + id
                response = await client.get(url)
                logging.info(f"[{time.strftime('%H:%M:%S')}] Received response from {url}, status: {response.status_code}")
                #insert id into results
                abstract = self.extract_summary(response.text)
                currArticle = Article(arxiv_id=id,abstract=abstract)
                currArticle = await self.store_results(currArticle)
                return response.status_code
            except httpx.HTTPStatusError as e:
                logging.error(f"[{time.strftime('%H:%M:%S')}] HTTP error: {e}")
                return e.response.status_code
            except httpx.RequestError as e:
                logging.error(f"[{time.strftime('%H:%M:%S')}] Request error: {e}")
                return None
            except Exception as e:
                logging.exception(e)
                logging.error("Failed to process paper")

    def extract_summary(self,html_content):
        # Parse HTML content with BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')

        # Find all blockquote tags containing blockquote tags
        blockquote = soup.find_all('blockquote')

        content_without_span = ''.join(blockquote[0].find_all(string=True, recursive=False)).strip()

        return content_without_span

    async def store_results(self,currArticle:Article)->Article:
        logging.info("Storing fetched abstract and writing to queue")
        
        try:
            async with get_session() as session:
                session.add(currArticle)  # Add the object to the session
                await session.commit()     # Save it to the database
                await session.refresh(currArticle) # Refresh to get the generated ID from the DB
                logging.info(f"Inserted article with id {currArticle.id}")
                return currArticle
        except Exception as e:
            logging.exception(e)
            logging.error("Error in saving article raw",str(e))



    async def fetch_ids(self, client:httpx.AsyncClient,limit: int) -> List[str]:
        IDlist = None
        try:
            if not settings.dummy:
                r = await client.get(baseURL)
                IDlist = self.extract_ids(r.text)
            else:
                async with aiofiles.open("list.txt", "r",encoding='utf-8') as f:
                    text = await f.read()
                    logging.debug(text[0:30])
                    IDlist = self.extract_ids(text)
            return IDlist
        except httpx.HTTPStatusError as e:
            logging.error(f"[{time.strftime('%H:%M:%S')}] HTTP error: {e}")
            return e.response.status_code
        except httpx.RequestError as e:
            logging.error(f"[{time.strftime('%H:%M:%S')}] Request error: {e}")
            return None









