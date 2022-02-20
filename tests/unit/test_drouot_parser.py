from unittest import TestCase

from fine_art_scrapper.parsers.identification_helpers import identify_author, identify_materials, identify_lot_id, \
    identify_estimation_and_price, identify_size


class TestParser(TestCase):

    def test_identify_author(self):
        tests = [
            "Jean-Sébastien D'ASNIERE POUET (1901-1965)",
            "Irène PAGES (1934)",
            "Ecole truc du 18ème",
            "Ecole truc vers 1890",
            "Dans le gout de Jean PIAIRRE",
            "D'après Frank RIBERA",
            "D'après RIBERA",
            "Dans le gout de BILLY"
        ]
        results = ["D'ASNIERE POUET", "PAGES", "truc", "truc", "PIAIRRE", "RIBERA", "RIBERA", "BILLY"]
        for t, r in zip(tests, results):
            rez = identify_author(t)
            self.assertNotEqual(rez, None, f"'{t}' failed the parsing")
            self.assertEqual(rez["surname"], r, f"No match {rez['surname']}!={r}")

    def test_material(self):
        strs = """
            Huile sur panneau
            Pastel et craie sur papier
            Pastel sur papier
            Pastel signé en bas à droite
            Huile sur toile, Huiles sur toile
            Aquarelle
            Aquarelle sur papier
            Deux aquarelles sur papier
            Deux huiles sur toile
            Huile sur panneau double face
            Gouache sur papier
            dessin et craie sur papier
            Gouache sur carton
            Importante Huile sur panneau, Cadre en bois sculpté et doré
        """
        tests = filter(lambda x: len(x) > 0, strs.strip(" ").split("\n"))

        for t in tests:
            rez = identify_materials(t)
            self.assertNotEqual(rez, None, f"'{t}' failed the parsing")

    def test_identify_lot_id(self):
        strs = """
        Lot n° 1
        Lot n° 1 bis
        Lot n° 1 ter
        Lot n° 123
        Lot  n° 1094829  ter
        """
        tests = filter(lambda x: len(x) > 0, strs.strip(" ").split("\n"))

        for t in tests:
            rez = identify_lot_id(t)
            self.assertNotEqual(rez, None, f"'{t}' failed the parsing")

    def test_identify_estimation_and_price(self):
        tests = [
            "Résultat : Non Communiqué / Estimation : 200 - 400 EUR",
            "Résultat :  Non Communiqué            /         Estimation :                200 - 400 EUR     ",
            "Résultat :  3\xa0100  EUR          /         Estimation :                200 - 400 EUR     ",
            "Résultat :  3\xa0100  EUR          /         Estimation :                200 - 3\xa0100 EUR     ",
            "Résultat :  Non Communiqué         /         Estimation :                Non Communiqué    "
            "Résultat : Non Communiqué "
        ]

        for t in tests:
            rez = identify_estimation_and_price(t)
            self.assertNotEqual(rez, None, f"'{t}' failed the parsing")

    def test_identify_size(self):
        tests = [
            "12 x 35",
            "17.5 x 11.5 cm",
            "18 x 25, 5 cm",
            "18 mm x 34 cm"
        ]
        results = [("12", "35"), ("17.5", "11.5"), ("18", "25, 5"), ("18", "34")]
        for t, r in zip(tests, results):
            rez = identify_size(t)
            self.assertNotEqual(rez, None, f"'{t}' failed the parsing")
            self.assertEqual(rez["height"], r[1], f"{rez['height']} did not match {r[1]}")
            self.assertEqual(rez["width"], r[0], f"{rez['width']} did not match {r[0]}")
