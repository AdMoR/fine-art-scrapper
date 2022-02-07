import datetime

import redis
from unittest import TestCase, mock

from fine_art_scrapper.drou_scrapper.scraper import GazetteDrouotScraper
from tests.utils.drouot_mock import drouot_query_multiplexer


class TestDroutScrapper(TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.scrapper = GazetteDrouotScraper(token=None)

    def test_result_parse(self):
        with mock.patch.object(self.scrapper, "url_to_soup", new=drouot_query_multiplexer):
            rez = self.scrapper.parse_result_page("test")
            self.assertGreater(len(rez), 0)

            self.assertSetEqual({int(e.lot_id) for e in rez}, {5, 40, 53, 65, 67})
            self.assertSetEqual({int(e.price) for e in rez}, {625, 100, 250, 150})

    def test_catalog_parse(self):
        with mock.patch.object(self.scrapper, "url_to_soup", new=drouot_query_multiplexer):
            rez = self.scrapper.parse_catalog_page("test", 0)
            self.assertGreater(len(rez), 0)

            self.assertTrue(any("Non Communiqué" not in e.estimation for e in rez))

    def test_catalog_lisitng_parse(self):
        my_redis_mock = mock.MagicMock(redis.StrictRedis)
        my_redis_mock.hget.return_value = None
        with mock.patch.object(self.scrapper, "url_to_soup", new=drouot_query_multiplexer):
            with mock.patch.object(self.scrapper, "redis_cli", new=my_redis_mock):
                print(self.scrapper.redis_cli.hget(1, 2))
                rez = self.scrapper.parse_listing_page(0)

                self.assertGreater(len(rez), 0)
                self.assertTrue(type(rez[0]), datetime.datetime)
                self.assertGreater(len(rez[0].catalog_elements), 0)
