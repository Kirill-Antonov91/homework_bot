import logging
import os
import sys
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

from exceptions import APIRequestError, IncorrectRequestStatus

load_dotenv()


PRACTICUM_TOKEN = os.getenv("SECRET_PRACTICUM_TOKEN")
TELEGRAM_TOKEN = os.getenv("SECRET_TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("SECRET_TELEGRAM_CHAT_ID")

RETRY_PERIOD = 600
ENDPOINT = "https://practicum.yandex.ru/api/user_api/homework_statuses/"
HEADERS = {"Authorization": f"OAuth {PRACTICUM_TOKEN}"}


HOMEWORK_VERDICTS = {
    "approved": "Работа проверена: ревьюеру всё понравилось. Ура!",
    "reviewing": "Работа взята на проверку ревьюером.",
    "rejected": "Работа проверена: у ревьюера есть замечания.",
}

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(stream=sys.stdout)
logger.addHandler(handler)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)


def check_tokens():
    """Проверяет наличие всех обязательных переменных окружения."""
    env_tokens = (
        PRACTICUM_TOKEN,
        TELEGRAM_CHAT_ID,
        TELEGRAM_TOKEN,
    )
    return all(env_tokens)


def send_message(bot, message):
    """Отправляет сообщение в Telegram чат."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        message = "Бот отправил сообщение в Telegram чат"
        logger.debug(message)
    except Exception as error:
        message = f"Сбой в отправке сообщения: {error}"
        logger.error(message)


def get_api_answer(timestamp):
    """Осуществляет запрос к эндпоинту API-сервиса."""
    payload = {"from_date": timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=payload)
    except requests.RequestException:
        message = "Ошибка при запросе к API"
        raise APIRequestError(message)
    if response.status_code != HTTPStatus.OK:
        message = "Статус запроса отличный от 200"
        raise IncorrectRequestStatus(message)
    return response.json()


def check_response(response):
    """Проверяет ответ API на соответствие."""
    if not isinstance(response, dict):
        message = (
            f"Ответ API не является словарём," f"тип ответа {type(response)}"
        )
        raise TypeError(message)

    checking_keys = (
        "homeworks",
        "current_date",
    )
    if not all(key in response for key in checking_keys):
        message = "В ответе API недостаточно ключей"
        raise KeyError(message)

    homeworks = response.get("homeworks")
    if not isinstance(homeworks, list):
        message = (
            f"Значение по ключу homeworks не является списком"
            f"тип значения ключа {type(homeworks)}"
        )
        raise TypeError(message)
    return homeworks


def parse_status(homework):
    """Проверяет статус домашней работы, формирует сообщение."""
    homework_name = homework.get("homework_name")
    if not homework_name:
        message = "Отсуствует наименование последней домашней работы"
        raise KeyError(message)

    homework_status = homework.get("status")
    if not homework_status:
        message = "Отсуствует статус последней домашней работы"
        raise KeyError(message)

    verdict = HOMEWORK_VERDICTS.get(homework_status)
    if not verdict:
        message = (
            "Вердикт по последней домашней"
            "работе нестандартный или отсуствует"
        )
        raise KeyError(message)
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    logger.debug("Бот запущен")

    if not check_tokens():
        message = (
            "Сбой в работе программы: "
            "отсутсвуют обязательные переменные"
            "окружения\n"
            "Работа программы остановлена"
        )
        logger.critical(message)
        sys.exit(message)

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    prev_homework_message = ""
    last_message = ""
    timestamp = int(time.time())

    while True:
        try:
            api_answer = get_api_answer(timestamp)
            last_homework = check_response(api_answer)
            if not last_homework:
                homework_message = "Нет домашки"
            else:
                homework_message = parse_status(last_homework[0])
            if prev_homework_message != homework_message:
                send_message(bot, f"Новый статус домашки: {homework_message}")
                prev_homework_message = homework_message
        except Exception as error:
            message = f"Сбой в работе программы: {error}"
            logger.error(message)
            if message != last_message:
                last_message = message
                send_message(bot, message)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == "__main__":
    main()
