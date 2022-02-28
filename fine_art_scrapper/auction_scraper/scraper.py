from typing import List
import requests
import logging
import redis
import os
from bs4 import BeautifulSoup
import pickle
from urllib.parse import urlencode, quote_plus

import time
from typing import List, Any

from fine_art_scrapper.utils.scraped_objects import ResultItem, CatalogItem


class AuctionFRScraper:

    def __init__(self):
        self.known = list()
        self.logger = logging.getLogger("AuctionScraper")
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:95.0) Gecko/20100101 Firefox/95.0",
            "Accept-Language": "fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3",
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"
        }
        self.redis_cli = redis.StrictRedis()
        self.cookies = self.acquire_auth()

    def acquire_auth(self):
        data = {
            "email": "adrien_morvan@hotmail.fr",
            "password": os.environ["password"]
        }
        encoded_data = urlencode(data)
        url = "https://www.auction.fr/_fr/collectionneur/authenticate/"
        req = requests.post(url, data=encoded_data, headers=self.headers)
        return req.cookies

    def run(self):
        for i in range(1, 626):
            print(f"Iteration {i}")
            checkpoint_path = f"./checkpoint_{i}"
            if os.path.exists(checkpoint_path):
                continue
            all_sale_elements = self.parse_listing_page(offset=i)
            pickle.dump({"last_iteration": i, "elements": all_sale_elements}, open(checkpoint_path, "wb"))
            for e in all_sale_elements:
                e.redis_serialize(self.redis_cli)

    def parse_listing_page(self, offset=0):
        """

        """
        time.sleep(0.1)
        listing_url = f"https://www.auction.fr/_fr/vente/passees/?search-filter=&search-filter=&search-filter=&from-date=&to-date=&affichage=&page={offset}"
        soup = self.url_to_soup(listing_url)
        sales = soup.find_all("div", class_="vente-passee")

        all_sale_elements = list()

        for i, s in enumerate(sales):
            sale_link = s.find("a", href=True)["href"]
            sale = self.parse_catalog_page(sale_link, list())
            all_sale_elements.append(sale)

        return all_sale_elements

    def parse_catalog_page(self, catalog_id: str, already_parsed: List[str]) -> List[CatalogItem]:
        """
        ex : catalog_id = "119697-3-suisses"
        """
        time.sleep(0.1)
        catalog_items = list()
        sale_url = "https://www.auction.fr" + catalog_id
        if sale_url in already_parsed:
            return list()
        already_parsed.append(sale_url)
        sale_soup = self.url_to_soup(sale_url)
        all_items = sale_soup.find_all("div", class_="card")

        for it in all_items:
            print(it)
            print("\n\n")
            lot_block = it.find("h5", class_="card-lot")
            if lot_block is None:
                continue
            lot_id = lot_block.text
            detail_link = it.find("a", href=True)["href"]
            title = it.find("h4", class_="card-title").text
            estimation_price = it.find("span", class_="card-price").text
            if it.find("span", class_="card-no-result") is not None:
                result_price = None
            else:
                result_price = it.find("span", class_="card-result").text

            detail = self.parse_lot_detail_page(detail_link)

            lot = {"id": lot_id, "link": detail_link, "title": title, "estimation": estimation_price,
                   "result": result_price, "detail": detail}

            catalog_items.append(lot)

        # Next page
        link = sale_soup.find("a", {"aria-label": "Next"}, href=True)
        if link is not None:
            new_link = link["href"]
            catalog_items.extend(self.parse_catalog_page(new_link, already_parsed))

        return catalog_items

    def parse_lot_detail_page(self, url):
        time.sleep(0.05)
        lot_url = "https://www.auction.fr" + url
        lot_soup = self.url_to_soup(lot_url)

        infos = lot_soup.find("div", class_="content-block")

        cblocks = lot_soup.find_all("div", class_="content-block")
        cat = list(filter(lambda x: "Catégories" in x.text, cblocks))[0].find("a", class_="btn").text

        return {"category": cat, "description": infos.text}

    def url_to_soup(self, url):
        rez = requests.get(url, headers=self.headers,
                           cookies=self.cookies)
        if rez.status_code != 200:
            raise Exception(f"Query failed for url : {url}")
        return BeautifulSoup(rez.text, 'html.parser')


if __name__ == "__main__":
    scraper = AuctionFRScraper()
    scraper.run()
