from unittest import TestCase

from fine_art_scrapper.parsers.helpers import identify_author, identify_materials


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