import requests
import logging
import dateparser
import redis
import datetime
import os
from bs4 import BeautifulSoup
import pickle

import time
import re
from typing import List, Any

from fine_art_scrapper.utils.scraped_objects import DroutSalesElement, ResultItem, CatalogItem


class GazetteDrouotScraper:

    def __init__(self, token="75107dc6-4d0e-4da3-8927-18946bebfea9"):
        self.token = token
        self.known = list()
        self.logger = logging.getLogger("GazetteDrouotScraper")
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
            results = s.find("div", class_="resultatLink")

            # 0 Get general info :
            title = s.find("h2", class_="nomVente").text
            who = s.find("h3", class_="etudeVente").text
            where = s.find("div", class_="lieuVente").text
            when = s.find("div", class_="dateVente").find("span", class_="capitalize").text.strip()
            when = dateparser.parse(when)

            if when.date() > datetime.date.today() - datetime.timedelta(days=7):
                self.logger.info("Sale is too young, skipping")
                continue

            sale_url_link = s.find("div", "lienInfosVentes").find("a", class_="dsi-modal-link")["data-dsi-url"]
            sale_id_match = re.search("/recherche/venteInfoPageVente/([0-9]+)\?nomExpert=.*", sale_url_link)
            sale_id = sale_id_match.groups()[0] if sale_id_match else None

            if sale_id is None:
                self.logger.warning(f"Nothing to parse for sale {s.title} given {sale_url_link}")
                continue

            if self.redis_cli.hget("sales", sale_id) is not None:
                self.logger.warning(f"We already know sale {sale_id}")
                continue

            # Opt 0.5 : get pubLink
            pubLink = s.find("div", class_="pubLink")

            # 1 - Parse the results if available
            try:
                result_link = results.find("a", href=True)["href"]
            except AttributeError:
                self.logger.info("href not found for result")
                result_link = None

            if result_link:
                result_id = result_link.split("/")[-1]
                result_elements = self.parse_result_page(result_id)
            else:
                result_elements = None

            time.sleep(0.1)

            # 2 - Parse the catalog listing if available
            try:
                catalog_link = catalog.find("a", href=True)["href"]
            except AttributeError:
                self.logger.info("href not found for catalog")
                catalog_link = None

            if catalog_link:
                catalog_id = catalog_link.split("/")[-1]
                catalog_elements = self.parse_catalog_page(catalog_id)
            else:
                catalog_elements = None

            # 3 - Add the recombined sale object into our scraped results
            my_element = DroutSalesElement(sale_id, title, who, where, when, catalog_elements, result_elements)
            all_sale_elements.append(my_element)

        return all_sale_elements

    def parse_catalog_page(self, catalog_id: int, offset: int = 0) -> List[CatalogItem]:
        """
        ex : catalog_id = "119697-3-suisses"
        """
        url = f"https://www.gazette-drouot.com/ventes-aux-encheres/{catalog_id}?controller=lot&offset={offset}"
        soup_ = self.url_to_soup(url)

        items = soup_.find_all("div", class_="row")
        all_elements = list()

        for it in items:
            imgLink = it.find("div", class_="imgLot")
            if imgLink is None:
                self.logger.debug("No imgLink, this is not a lot")
                continue
            if "Réservé aux abonnés" in it.text:
                raise Exception("Token has expired")
            lot_id = imgLink.find("a", href=True)["href"]
            description = it.find("div", class_="descriptionLot")
            prez = description.find("div", class_="lotPresentation")
            resulat = description.find("div", class_="lotResulatListe")
            estimation = description.find("div", class_="lotEstimationListe")

            artiste = description.find("div", class_="lotArtisteListe")
            description_part = description.find("div", class_="lotDescriptionListe")

            all_elements.append(CatalogItem(
                catalog_id=catalog_id,
                lot_id=lot_id,
                presentation=prez.text if prez else None,
                result=resulat.text if resulat else None,
                estimation=estimation.text if estimation else None
            )
            )

        if len(all_elements) >= 50:
            time.sleep(0.1)
            all_elements.extend(
                self.parse_catalog_page(catalog_id, offset=offset + 50)
            )

        return all_elements

    def parse_result_page(self, result_id: int):
        other_url = f"https://www.gazette-drouot.com/catalogue/resultats/{result_id}"
        result_soup = self.url_to_soup(other_url)

        listing = result_soup.find_all("div", class_="lots-item")
        elements = list()
        for l in listing:
            elements.append(self.parse_lot_result(l, result_id))

        return elements

    def parse_lot_result(self, lot_obj: Any, result_id: int) -> ResultItem:
        """
        listing = result_soup.find_all("div", class_="lots-item")

        for l in listing:
            this_code
        """
        lot_id = None
        price = None

        e = lot_obj.find("div")
        groups = re.search("Lot ([0-9]+\s?.*\s?) :", e.text)
        if groups:
            lot_id = groups[1]

        price_div = lot_obj.text
        groups = re.search(".* ([0-9]+) €.*", price_div)
        if groups:
            price = groups[1]

        return ResultItem(result_id=result_id, lot_id=lot_id, price=price, currency="euro")

    def parse_lot_detail_page(self, url):
        soup = self.url_to_soup(url)

        time.sleep(0.05)
        page_description = soup.find("div", class_="lotDescriptionFiche").find("h2").text

        return page_description

    def url_to_soup(self, url):
        rez = requests.get(url, headers=self.headers,
                           cookies={"SESSION": self.token})
        if rez.status_code != 200:
            raise Exception(f"Query failed for url : {url}")
        return BeautifulSoup(rez.text, 'html.parser')


if __name__ == "__main__":
    scraper = GazetteDrouotScraper("8c63cd61-7930-49ce-96ec-412d0a426cb3")
    scraper.run()
