import os
import tempfile
import unittest
from unittest.mock import Mock, patch
import requests
from card_validator import CardValidator
from exceptions import InputDataError, NetworkError


class TestCardValidator(unittest.TestCase):
    # Проверка корректных номеров карт (Visa, MasterCard, МИР)
    def test_valid_cards(self) -> None:
        self.assertTrue(CardValidator.is_valid_card("4532015112830366"))          # Visa 16
        self.assertTrue(CardValidator.is_valid_card("4532 0151 1283 0366"))       # Visa с пробелами
        self.assertTrue(CardValidator.is_valid_card("4532-0151-1283-0366"))       # Visa с дефисами
        self.assertTrue(CardValidator.is_valid_card("4532015112830"))             # Visa 13 цифр
        self.assertTrue(CardValidator.is_valid_card("5425 2334 3010 9903"))       # MasterCard 54xx
        self.assertTrue(CardValidator.is_valid_card("2701 0000 0000 0008"))       # MasterCard 2701
        self.assertTrue(CardValidator.is_valid_card("2720 0000 0000 0005"))       # MasterCard 2720
        self.assertTrue(CardValidator.is_valid_card("2200 7001 2345 6781"))       # МИР

    # Проверка граничных значений диапазонов платежных систем
    def test_prefix_boundaries(self) -> None:
        self.assertTrue(CardValidator.is_valid_card("6221 2600 0000 0000", use_luhn=False))
        self.assertFalse(CardValidator.is_valid_card("2721 0000 0000 0004", use_luhn=False))
        self.assertFalse(CardValidator.is_valid_card("2220 0000 0000 0000", use_luhn=False))
        self.assertFalse(CardValidator.is_valid_card("2205 0000 0000 0000", use_luhn=False))

    # Проверка контрольной суммы по алгоритму Луна
    def test_luhn_check(self) -> None:
        bad_luhn = "4532 0151 1283 0367"
        self.assertFalse(CardValidator.is_valid_card(bad_luhn, use_luhn=True))
        self.assertTrue(CardValidator.is_valid_card(bad_luhn, use_luhn=False))

    # Проверка некорректной длины, смешанных разделителей и пустого ввода
    def test_invalid_cards(self) -> None:
        self.assertFalse(CardValidator.is_valid_card("1234 5678 9012 3456"))      # неверный префикс
        self.assertFalse(CardValidator.is_valid_card("453201511283"))             # 12 цифр (короткая)
        self.assertFalse(CardValidator.is_valid_card("4532 0151 1283"))           # 12 цифр с пробелами
        self.assertFalse(CardValidator.is_valid_card("4532 0151 1283 0366 1234")) # 20 цифр (длинная)
        self.assertFalse(CardValidator.is_valid_card("4532-0151 1283-0366"))      # смешанные разделители
        self.assertFalse(CardValidator.is_valid_card("4532 01511283 0366"))       # неполные разделители
        self.assertFalse(CardValidator.is_valid_card("4532_0151_1283_0366"))      # нижнее подчеркивание
        self.assertFalse(CardValidator.is_valid_card("4532 015a 1283 0366"))      # буквы

        with self.assertRaises(InputDataError):
            CardValidator.is_valid_card("   ")

    # Поиск в строке текста (с проверкой Луна и без нее)
    def test_find_in_text(self) -> None:
        text = (
            "Основная карта: 4532-0151-1283-0366, запасная: 5425 2334 3010 9903. "
            "Неверная сумма: 4532015112830367. Длинное число: 453201511283036612345."
        )
        self.assertEqual(
            CardValidator.find_in_text(text, use_luhn=True),
            ["4532-0151-1283-0366", "5425 2334 3010 9903"],
        )
        self.assertEqual(
            CardValidator.find_in_text(text, use_luhn=False),
            ["4532-0151-1283-0366", "5425 2334 3010 9903", "4532015112830367"],
        )

    # Поиск в файле
    def test_find_in_file(self) -> None:
        with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as tmp:
            tmp.write("Счет №1.\nКарта: 2200 7001 2345 6781.\n")
            tmp_path = tmp.name

        try:
            found = CardValidator.find_in_file(tmp_path)
            self.assertEqual(found, ["2200 7001 2345 6781"])
        finally:
            os.remove(tmp_path)

    # Обработка ошибок при работе с файлами
    def test_file_errors(self) -> None:
        with self.assertRaises(InputDataError):
            CardValidator.find_in_file("")

        with self.assertRaises(FileNotFoundError):
            CardValidator.find_in_file("no_such_file.txt")

        with tempfile.NamedTemporaryFile("wb", delete=False) as tmp:
            tmp.write(b"\xff\xfe\xfd")
            bad_path = tmp.name

        try:
            with self.assertRaises(InputDataError):
                CardValidator.find_in_file(bad_path)
        finally:
            os.remove(bad_path)

    # Поиск по URL (с имитацией HTTP-запроса)
    @patch("card_validator.requests.get")
    def test_find_on_url(self, mock_get: Mock) -> None:
        mock_resp = Mock()
        mock_resp.text = "<html><body>Карта для перевода: 4532 0151 1283 0366</body></html>"
        mock_resp.raise_for_status = Mock()
        mock_get.return_value = mock_resp

        found = CardValidator.find_on_url("example.com")
        self.assertEqual(found, ["4532 0151 1283 0366"])
        mock_get.assert_called_once_with("https://example.com", timeout=10)

    # Обработка сетевых ошибок и пустого URL
    @patch("card_validator.requests.get")
    def test_url_errors(self, mock_get: Mock) -> None:
        with self.assertRaises(InputDataError):
            CardValidator.find_on_url("  ")

        mock_get.side_effect = requests.RequestException("Timeout")
        with self.assertRaises(NetworkError):
            CardValidator.find_on_url("https://example.com")


if __name__ == "__main__":
    unittest.main()
