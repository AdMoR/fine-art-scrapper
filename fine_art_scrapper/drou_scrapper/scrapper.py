import requests
import json
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
from typing import NamedTuple, List, Dict, Any


class ResultItem(NamedTuple):
    result_id: int
    lot_id: int
    price: float
    currency: str

    def to_json(self):
        return {"result_id": self.result_id, "lot_id": self.lot_id, "price": self.price, "currency": self.currency}


class CatalogItem(NamedTuple):
    catalog_id: int
    lot_id: int
    presentation: str
    result: str
    estimation: str

    def to_json(self):
        return {"catalog_id": self.catalog_id, "lot_id": self.lot_id, "presentation": self.presentation,
                "result": self.result, "estimation": self.estimation}


class DroutSalesElement(NamedTuple):
    catalog_id: int
    title: str
    who: str
    where: str
    catalog_elements: List[CatalogItem]
    result_elements: List[ResultItem]
    is_passed: bool = False

    @property
    def catalog_df(self):
        return pd.DataFrame(self.catalog_elements)

    @property
    def result_df(self):
        return pd.DataFrame(self.result_elements)

    def redis_serialize(self, redis_cli):
        # Rule : do not serialize active sales, we assume all infos will remain after
        if not self.is_passed:
            return
        if redis_cli.hget("sales", self.catalog_id) is None:
            redis_cli.hset("sales", self.catalog_id,
                           json.dumps({"id": self.catalog_id, "title": self.title, "who": self.who, "where": self.where})
                           )
            for cata in self.catalog_elements:
                redis_cli.hset("catalog_item", cata.lot_id, cata.to_json())
            for rez in self.result_elements:
                redis_cli.hset("result_item", rez.result_id, rez.to_json())


class GazetteDrouotScraper:

    def __init__(self, token="75107dc6-4d0e-4da3-8927-18946bebfea9"):
        self.token = token
        self.known = list()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:95.0) Gecko/20100101 Firefox/95.0",
            "Accept-Language": "fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3",
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"
        }

    def run(self):
        pass

    def parse_listing_page(self, offset=0):
        # url = "https://www.gazette-drouot.com/ventes-aux-encheres/resultats-ventes?offset=24850&max=50#modal-content2"
        new_url = f"https://www.gazette-drouot.com/ventes-aux-encheres/passees?offset={offset}&max=50"
        soup = self.url_to_soup(new_url)
        sales = soup.find_all("div", class_="infosVente")

        all_sale_elements = list()

        for s in sales:
            time.sleep(0.1)
            catalog = s.find("div", class_="catalogueLink")
            results = s.find("div", class_="resultatLink")

            # 0 Get general info :
            title = s.find("h2", class_="nomVente").text
            who = s.find("h3", class_="etudeVente").text
            where = s.find("div", class_="lieuVente").text
            sale_url_link = s.find("div", "lienInfosVentes").find("a", class_="dsi-modal-link")["data-dsi-url"]
            sale_id_match = re.search("/recherche/venteInfoPageVente/([0-9]+)?nomExpert=.*", sale_url_link)
            sale_id = sale_id_match.groups[1]
            # Opt 0.5 : get pubLink
            pubLink = s.find("div", class_="pubLink")

            # 1 - Parse the results if available
            try:
                result_link = results.find("a", href=True)["href"]
            except AttributeError:
                print("href not found for result")
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
                print("href not found for catalog")
                catalog_link = None

            if catalog_link:
                catalog_id = catalog_link.split("/")[-1]
                catalog_elements = self.parse_catalog_page(catalog_id)
            else:
                catalog_elements = None

            # 3 - Add the recombined sale object into our scraped results
            my_element = DroutSalesElement(sale_id, title, who, where, catalog_elements, result_elements)
            all_sale_elements.append(my_element)

        return all_sale_elements

    def parse_result_page(self, result_id: int):
        other_url = f"https://www.gazette-drouot.com/catalogue/resultats/{result_id}"
        result_soup = self.url_to_soup(other_url)

        listing = result_soup.find_all("div", class_="lots-item")
        elements = list()
        for l in listing:
            elements.append(self.parse_lot_result(l, result_id))

        return elements

    def parse_catalog_page(self, catalog_id: int, offset: int = 0) -> List[CatalogItem]:
        """
        ex : catalog_id = "119697-3-suisses"
        """
        url = f"https://www.gazette-drouot.com/ventes-aux-encheres/{catalog_id}?controller=lot&offset={offset}"
        print(url)
        soup_ = self.url_to_soup(url)

        items = soup_.find_all("div", class_="row")
        all_elements = list()

        for it in items:
            imgLink = it.find("div", class_="imgLot")
            if imgLink is None:
                print("No imgLink, this is not a lot")
                continue
            lot_id = imgLink.find("a", href=True)["href"]
            description = it.find("div", class_="descriptionLot")
            prez = description.find("div", class_="lotPresentation")
            resulat = description.find("div", class_="lotResulatListe")
            estimation = description.find("div", class_="lotEstimationListe")

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

    def url_to_soup(self, url):
        rez = requests.get(url, headers=self.headers,
                           cookies={"SESSION": self.token})
        if rez.status_code != 200:
            raise Exception(f"Query failed for url : {url}")
        return BeautifulSoup(rez.text, 'html.parser')
