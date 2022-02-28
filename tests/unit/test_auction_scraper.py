import datetime
import os

import redis
from unittest import TestCase, mock

from fine_art_scrapper.auction_scraper.scraper import AuctionFRScraper
from tests.utils.auction_mock import auction_query_multiplexer


class TestAuctionScrapper(TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        os.environ["password"] = "toto"
        cls.scrapper = AuctionFRScraper()

    def test_lot_parse(self):
        with mock.patch.object(self.scrapper, "url_to_soup", new=auction_query_multiplexer):
            rez = self.scrapper.parse_lot_detail_page("/_fr/lot/ecole-italienne-de-la-fin-du-xviie-siecle-feuille-d-etude-recto-verso-christ-au-18404824")
            self.assertGreater(len(rez), 0)
            self.assertSetEqual(set(rez.keys()), {"category", "description"})

    def test_catalog_parse(self):
        with mock.patch.object(self.scrapper, "url_to_soup", new=auction_query_multiplexer):
            rez = self.scrapper.parse_catalog_page(
                "/_fr/vente/collection-ulmann-mille-dessins-de-giulio-romano-a-maurice-denis-deuxieme-jour-de-vente-70418?query=&numero=&affichage=", list())
            self.assertGreater(len(rez), 0)

            self.assertTrue(any("Non Communiqué" not in e["estimation"] for e in rez))

    def test_catalog_lisitng_parse(self):
        my_redis_mock = mock.MagicMock(redis.StrictRedis)
        my_redis_mock.hget.return_value = None
        with mock.patch.object(self.scrapper, "url_to_soup", new=auction_query_multiplexer):
            with mock.patch.object(self.scrapper, "redis_cli", new=my_redis_mock):
                rez = self.scrapper.parse_listing_page(0)

                self.assertGreater(len(rez), 0)
                self.assertTrue(type(rez[0]), datetime.datetime)
                self.assertGreater(len(rez[0].catalog_elements), 0)
