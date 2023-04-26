class IncorrectRequestStatus(Exception):
    """Класс исключения при получении некорректного статуса запроса к API."""


class APIRequestError(Exception):
    """Класс исключения при ошибке запроса к API."""


class MessageSendError(Exception):
    """Ошибка отправки сообщения в Телеграм."""
