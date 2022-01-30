from unittest import TestCase, mock

from fine_art_scrapper.drou_scrapper.scrapper import GazetteDrouotScraper
from tests.utils.drouot_mock import drouot_query_multiplexer


class TestDroutScrapper(TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.scrapper = GazetteDrouotScraper(token=None)

    def test(self):
        with mock.patch.object(self.scrapper, "url_to_soup", new=drouot_query_multiplexer):
            rez = self.scrapper.parse_result_page("test")
            self.assertGreater(len(rez), 0)

    def test(self):
        with mock.patch.object(self.scrapper, "url_to_soup", new=drouot_query_multiplexer):
            rez = self.scrapper.parse_catalog_page("test", 0)
            self.assertGreater(len(rez), 0)
