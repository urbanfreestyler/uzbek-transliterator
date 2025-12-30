import unittest
from transliterate import to_cyrillic, to_latin


class TestTransliterator(unittest.TestCase):

    def test_basic_cyrillic(self):
        self.assertEqual(to_cyrillic("salom"), "салом")
        self.assertEqual(to_cyrillic("men"), "мен")

    def test_basic_latin(self):
        self.assertEqual(to_latin("салом"), "salom")
        self.assertEqual(to_latin("мен"), "men")

    def test_soft_sign_words(self):
        self.assertEqual(to_cyrillic("avtomobil"), "автомобиль")
        self.assertEqual(to_cyrillic("Avtomobil"), "Автомобиль")

    def test_ts_exception_words(self):
        # aberratsion -> аберрацион (aberra(ts)ion)
        self.assertEqual(to_cyrillic("aberratsion"), "аберрацион")
        # abs(s)ess -> абсцесс
        self.assertEqual(to_cyrillic("abssess"), "абсцесс")

    def test_ye_exception_words(self):
        # konve(ye)r -> конвейер
        self.assertEqual(to_cyrillic("konveyer"), "конвейер")
        # i(ye) -> ийе
        self.assertEqual(to_cyrillic("iye"), "ийе")

    def test_sh_exception_words(self):
        # a(sh)ob -> асҳоб
        self.assertEqual(to_cyrillic("ashob"), "асҳоб")

    def test_compounds(self):
        self.assertEqual(to_cyrillic("shahar"), "шаҳар")
        self.assertEqual(to_cyrillic("choy"), "чой")

    def test_contextual_ye(self):
        self.assertEqual(to_cyrillic("yetti"), "етти")
        self.assertEqual(to_cyrillic("maye"), "мае")
        self.assertEqual(to_cyrillic("ertaga"), "эртага")

    def test_contextual_ts_cyr_to_lat(self):
        self.assertEqual(to_latin("цирк"), "sirk")
        self.assertEqual(to_latin("федерация"), "federatsiya")
        self.assertEqual(to_latin("функция"), "funksiya")


if __name__ == "__main__":
    unittest.main()
