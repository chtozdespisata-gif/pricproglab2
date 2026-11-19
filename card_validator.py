import re
import requests
from exceptions import InputDataError, NetworkError


class CardValidator:
    # Регулярное выражение для поиска номеров карт (Visa, MasterCard, МИР, Maestro, UnionPay)
    # Поддерживает слитное написание, а также разделение пробелами или дефисами (единый разделитель)
    CARD_PATTERN = re.compile(
        r"(?<!\d)"
        r"(?:"
        r"4\d{3}(?P<sep1>[ -]?)\d{4}(?P=sep1)\d{4}(?:(?P=sep1)\d{4}(?:(?P=sep1)\d{1,3})?|(?P=sep1)\d{1,3})|"
        r"(?:5[1-5]\d{2}|222[1-9]|22[3-9]\d|2[3-6]\d{2}|270\d|271\d|2720)(?P<sep2>[ -]?)\d{4}(?:(?P=sep2)\d{4}){2}|"
        r"220[0-4](?P<sep3>[ -]?)\d{4}(?:(?P=sep3)\d{4}){2}|"
        r"(?:5018|5020|5038|5893|6304|6759|676[1-3])(?P<sep4>[ -]?)\d{4}(?P=sep4)\d{4}(?:(?P=sep4)\d{4}(?:(?P=sep4)\d{1,3})?|(?P=sep4)\d{1,3})|"
        r"62\d{2}(?P<sep5>[ -]?)\d{4}(?:(?P=sep5)\d{4}){2}(?:(?P=sep5)\d{1,3})?"
        r")"
        r"(?!\d)"
    )

    @staticmethod
    def clean_number(card_str: str) -> str:
        return re.sub(r"[ -]", "", card_str)

    @classmethod
    def check_luhn(cls, card_str: str) -> bool:
        digits_str = cls.clean_number(card_str)
        if not digits_str.isdigit():
            return False

        digits = [int(d) for d in digits_str]
        total = 0
        is_second = False

        for d in reversed(digits):
            if is_second:
                d *= 2
                if d > 9:
                    d -= 9
            total += d
            is_second = not is_second

        return total % 10 == 0

    @classmethod
    def is_valid_card(cls, card_str: str, use_luhn: bool = True) -> bool:
        text = card_str.strip()
        if not text:
            raise InputDataError("Номер карты не может быть пустым")

        if not cls.CARD_PATTERN.fullmatch(text):
            return False

        if use_luhn:
            return cls.check_luhn(text)
        return True

    @classmethod
    def find_in_text(cls, text: str, use_luhn: bool = True) -> list[str]:
        matches = [m.group(0) for m in cls.CARD_PATTERN.finditer(text)]
        if not use_luhn:
            return matches

        return [item for item in matches if cls.check_luhn(item)]

    @classmethod
    def find_in_file(cls, path: str, use_luhn: bool = True) -> list[str]:
        if not path.strip():
            raise InputDataError("Путь к файлу не указан")

        try:
            with open(path.strip(), "r", encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            raise InputDataError("Файл должен быть текстовым в кодировке UTF-8")

        return cls.find_in_text(content, use_luhn=use_luhn)

    @classmethod
    def find_on_url(cls, url: str, use_luhn: bool = True) -> list[str]:
        target_url = url.strip()
        if not target_url:
            raise InputDataError("URL не может быть пустым")

        if not target_url.startswith(("http://", "https://")):
            target_url = "https://" + target_url

        try:
            response = requests.get(target_url, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            raise NetworkError(f"Не удалось загрузить страницу: {e}")

        return cls.find_in_text(response.text, use_luhn=use_luhn)
