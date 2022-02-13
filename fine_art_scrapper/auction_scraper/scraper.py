import requests
import logging
import redis
import os
from bs4 import BeautifulSoup
import pickle

import time
from typing import List, Any

from fine_art_scrapper.utils.scraped_objects import ResultItem, CatalogItem


class GazetteDrouotScraper:

    def __init__(self, token="75107dc6-4d0e-4da3-8927-18946bebfea9"):
        self.token = token
        self.known = list()
        self.logger = logging.getLogger("AuctionScraper")
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:95.0) Gecko/20100101 Firefox/95.0",
            "Accept-Language": "fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3",
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"
        }
        self.redis_cli = redis.StrictRedis()

    def run(self):
        for i in range(0, 2049):
            print(f"Iteration {i}")
            checkpoint_path = f"./checkpoint_{i}"
            if os.path.exists(checkpoint_path):
                continue
            all_sale_elements = self.parse_listing_page(offset=50*i)
            pickle.dump({"last_iteration": i, "elements": all_sale_elements}, open(checkpoint_path, "wb"))
            for e in all_sale_elements:
                e.redis_serialize(self.redis_cli)

    def parse_listing_page(self, offset=0):
        """
        Example of url parsed : url =
        https://www.gazette-drouot.com/ventes-aux-encheres/resultats-ventes?offset=24850&max=50#modal-content2

        In hierarchy :

        parse_listing_page(offset=0)
         - parse_catalog_page(sale_a), parse_result_page(sale_a)
         - parse_catalog_page(sale_b), parse_result_page(sale_b)
         - ...

        parse_listing_page(offset=50)
         - parse_catalog_page(sale_u), parse_result_page(sale_u)
         - parse_catalog_page(sale_v), parse_result_page(sale_v)
        """
        new_url = f"https://www.gazette-drouot.com/ventes-aux-encheres/passees?offset={offset}&max=50"
        soup = self.url_to_soup(new_url)
        sales = soup.find_all("div", class_="infosVente")

        all_sale_elements = list()

        for i, s in enumerate(sales):
            time.sleep(0.1)
            catalog = s.find("div", class_="catalogueLink")
            pass

    def parse_catalog_page(self, catalog_id: int, offset: int = 0) -> List[CatalogItem]:
        """
        ex : catalog_id = "119697-3-suisses"
        """
        pass

    def parse_result_page(self, result_id: int):
        pass

    def parse_lot_result(self, lot_obj: Any, result_id: int) -> ResultItem:
        """
        listing = result_soup.find_all("div", class_="lots-item")

        for l in listing:
            this_code
        """
        pass

    def parse_lot_detail_page(self, url):
        pass

    def url_to_soup(self, url):
        rez = requests.get(url, headers=self.headers,
                           cookies={"SESSION": self.token})
        if rez.status_code != 200:
            raise Exception(f"Query failed for url : {url}")
        return BeautifulSoup(rez.text, 'html.parser')


if __name__ == "__main__":
    scraper = GazetteDrouotScraper("8c63cd61-7930-49ce-96ec-412d0a426cb3")
    scraper.run()
