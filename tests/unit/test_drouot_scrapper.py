from unittest import TestCase

from fine_art_scrapper.drou_scrapper.scrapper import GazetteDrouotScraper


class TestDroutScrapper(TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.scrapper = GazetteDrouotScraper(token=None)

    def test(self):
        pass
