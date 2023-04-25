class IncorrectRequestStatus(Exception):
    """Класс исключения при получении некорректного статуса запроса к API."""

    pass


class APIRequestError(Exception):
    """Класс исключения при ошибке запроса к API."""

    pass
