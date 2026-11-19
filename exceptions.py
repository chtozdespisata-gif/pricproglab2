class CardError(Exception):
    """Базовая ошибка приложения."""


class InputDataError(CardError):
    """Ошибка во входных данных."""


class NetworkError(CardError):
    """Ошибка при загрузке веб-страницы."""
