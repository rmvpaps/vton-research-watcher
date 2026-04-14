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
from shared import ArticleBase,get_session,settings
from typing import List
from scraper.base_scraper import BaseScraper
import re

CONCURRENCY_LIMIT = settings.scrape_concurrency
ARXIV_ABS_URL = "https://arxiv.org/abs/"

class HtmlStructureException(ValueError):
    pass


class HtmlScraper(BaseScraper):
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.curr_num = 0
        self.semaphore = asyncio.Semaphore(settings.scrape_concurrency)


            
    def extract_info_from_listing(self,html_content:str) -> List[str]:

        try:
            # Parse HTML content with BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')

            # Find all dl tags containing dt tags
            dl_tags = soup.find_all('dl')

            # List to store extracted IDs
            extracted_ids = []
            total_pages = -1

            # Iterate through dl tags
            for dl_tag in dl_tags:
                # Find all dt tags within the current dl tag
                dt_tags = dl_tag.find_all('dt')

                # Iterate through dt tags
                for dt_tag in dt_tags:
                    logging.debug(dt_tag)
                    try:
                
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
                    except Exception as e:
                        logging.error(f"Error in extracting Id from dt_tag {e}")
            try:
                pg_tag = soup.find('div',attrs={'class':'paging'})
                pg_info_str = pg_tag.find(string=True,recursive=False)
                digits = re.findall(r'\d+', pg_info_str)
                total_pages = int("".join(digits))
            except Exception as e:
                logging.error(f"Error in finding total items in the week {e}")
                #raise HtmlStructureException("Unexpected HTML format. Total could not be extracted")

        except Exception as e:
            logging.error(f"Error in extracting ids - tag structure {e}")
            raise HtmlStructureException("Unexpected HTML format.IDs could not be extracted")
        
        if len(extracted_ids)== 0:
            logging.error(f"Error in extracting ids - tag structure")
            raise HtmlStructureException("Unexpected HTML format.IDs could not be extracted")

        return extracted_ids,total_pages
    
    async def get_details_batch(self, client: httpx.AsyncClient, id_list: List[str]) -> List[ArticleBase]:
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

    async def fetchPaperDetails(self,client:httpx.AsyncClient, id:str)->ArticleBase:
        async with self.semaphore:
            print("Fetch individual abstract")
            try:
                url = ARXIV_ABS_URL + id
                response = await client.get(url)
                logging.info(f"[{time.strftime('%H:%M:%S')}] Received response from {url}, status: {response.status_code}")
                #insert id into results
                abstract,title = self.extract_summary_title(response.text)
                currArticle = ArticleBase(arxiv_id=id,abstract=abstract,title=title)
                return currArticle
                # currArticle = await self.store_results(currArticle)
                # return response.status_code
            except httpx.HTTPStatusError as e:
                logging.error(f"[{time.strftime('%H:%M:%S')}] HTTP error: {e}")
                return e.response.status_code
            except httpx.RequestError as e:
                logging.error(f"[{time.strftime('%H:%M:%S')}] Request error: {e}")
                return None
            except Exception as e:
                logging.exception(e)
                logging.error("Failed to process paper")

    def extract_summary_title(self,html_content):
        summary = None
        title = None
        # Parse HTML content with BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')

        try:

            # Find all blockquote tags containing blockquote tags
            blockquote = soup.find_all('blockquote')

            summary = ''.join(blockquote[0].find_all(string=True, recursive=False)).strip()
        except Exception as e:
            logging.error(f"Error in extracting summary {e}")
            raise HtmlStructureException("Invalid structure - Could not extract Summary")

        try:
            
            # Find all blockquote tags containing blockquote tags
            headings = soup.find('div',attrs={'id':'abs'}).find('h1')

            title = ''.join(headings.find_all(string=True, recursive=False)).strip()
        except Exception as e:
            logging.error(f"Error in extracting title {e}")
            raise HtmlStructureException("Invalid structure. Could not extract title")

        return summary,title



    async def fetch_id_list_paging(self, client:httpx.AsyncClient,skip: int=0,show:int=25) -> List[str]:
        async with self.semaphore:
            print("Fetch new page for listing from",skip)
            IDlist = None
            try:

                r = await client.get(f"{settings.baseURL}?skip={skip}&show={show}")
                IDlist,total = self.extract_info_from_listing(r.text)
                return IDlist,total
            except httpx.HTTPStatusError as e:
                logging.error(f"[{time.strftime('%H:%M:%S')}] HTTP error: {e}")
                return e.response.status_code
            except httpx.RequestError as e:
                logging.error(f"[{time.strftime('%H:%M:%S')}] Request error: {e}")
                return None
            except HtmlStructureException as e:
                logging.error(f"Parsing error {e}")
                return None



    async def fetch_ids(self, client:httpx.AsyncClient,limit: int) -> List[str]:
        IDlist = None
  


        IDlist,total = await self.fetch_id_list_paging(client)

        if total > len(IDlist) and limit>len(IDlist):
            print("Need to fetch more")
            if limit > total:
                limit = total
            #spawn more tasks to get the results
            tasks = []
            show = 25
            try:
                async with asyncio.TaskGroup() as tg:
                    for skip in range(show,limit,show):
                        # We create and store task references to collect results later
                        task = tg.create_task(self.fetch_id_list_paging(client, skip=skip,show=show))
                        tasks.append(task)
            except ExceptionGroup as eg:
                logging.error(f"Batch processing encountered errors: {eg}")

            # Collect results from tasks that succeeded
            results =  [
                item 
                for t in tasks 
                if not t.cancelled() and (res := t.result()) is not None 
                for item in res[0]
            ]
            if len(results)!= 0:
                IDlist.extend(results)
            if len(IDlist) > limit:
                IDlist = IDlist[0:limit]
        return IDlist










