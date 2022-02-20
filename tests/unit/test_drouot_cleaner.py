from unittest import TestCase

from fine_art_scrapper.parsers.cleaning_helpers import handle_missing_line_return


class TestDrouotCleaner(TestCase):

    def test_new_line_addition(self):
        tests = [
            "Un exemple normal avec un autheur Jean PIAIRRE",
            "Un exemple problématique.Daté de 1985.Aucun problème",
            "Un exemple problématiqueDaté de 1985Aucun problème",
        ]
        results = [
            "Un exemple normal avec un autheur Jean PIAIRRE",
            "Un exemple problématique.Daté de 1985.Aucun problème",
            "Un exemple problématique\nDaté de 1985\nAucun problème"
        ]

        for t, r in zip(tests, results):
            rez = handle_missing_line_return(t)
            self.assertEqual(rez, r)
