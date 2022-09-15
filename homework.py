from __future__ import annotations
import os
import sys
import time
import logging
from typing import Optional, Any

import telegram
from dotenv import load_dotenv
import requests
from telegram import Bot

load_dotenv()

JSONType = dict[str, Any] # SKTODO use TypedDict

PRACTICUM_TOKEN: Optional[str] = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN: Optional[str] = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID: Optional[str] = os.getenv('TELEGRAM_CHAT_ID')

ENDPOINT: str = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS: dict[str, str] = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
RETRY_TIME: int = 10 # SKTODO set value 600

# Keys of the response of the ENDPOINT API:
CURRENT_DATE: str = 'current_date'
HOMEWORKS: str = 'homeworks'
# Keys in an element in `HOMEWORKS` array:
HOMEWORK_NAME: str = 'homework_name'
STATUS: str = 'status'

HOMEWORK_STATUSES: dict[str, str] = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


class PracticumAPIError(Exception):
    pass


class UnsetEnvVarException(Exception):
    pass


handlers = (logging.StreamHandler(stream=sys.stdout), )
logging.basicConfig(
        format='%(asctime)s [%(levelname)s] %(message)s',
        level=logging.DEBUG,
        handlers=handlers
)


def send_message(bot: Bot, message: str) -> None:
    bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message
    )


# SKTODO current_timestamp Optional or float?
def get_api_answer(current_timestamp: Optional[float] = None) -> JSONType:
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}

    response = requests.get(
            url=ENDPOINT,
            headers=HEADERS,
            params=params
    )
    response.raise_for_status()
    info: JSONType = response.json()
    return info


def check_response(response: JSONType) -> list[JSONType]:
    try:
        homeworks: list[JSONType] = response[HOMEWORKS]
        _ = response[CURRENT_DATE]
    except TypeError as e:
        raise type(e)(f'{e} - "{response}" is not a {JSONType} type')
    except KeyError as e:
        raise PracticumAPIError(f'There is no "{e}" key in API response')

    if isinstance(homeworks, list):
        return homeworks
    else:
        raise PracticumAPIError(
                f'{type(homeworks)} is not `list` type value'
        )


def parse_status(homework: JSONType) -> str:
    try:
        homework_name = homework[HOMEWORK_NAME]
        homework_status = homework[STATUS]
    except KeyError as e:
        raise PracticumAPIError(f'There is no {e} key in API response')

    try:
        verdict = HOMEWORK_STATUSES[homework_status]
    except KeyError as e:
        raise PracticumAPIError(f'There is no {e} in {HOMEWORK_STATUSES}')

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens() -> bool:
    """
    Checks for the presence of all required variables from the environment.
    """
    tokens = {
            'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
            'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID,
            'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
    }
    for name, token in tokens.items():
        if not token:
            logging.critical(
                    f'Отсутствует обязательная переменная окружения `{name}`'
            )
            return False
    return True


def main() -> None:
    """Основная логика работы бота."""

    if not check_tokens():
        sys.exit(0)
        # raise UnsetEnvVarException('Not all environment variables are set')

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())

    cached_message: Optional[str] = None
    message: Optional[str] = None
    while True:
        try:
            response = get_api_answer(current_timestamp=current_timestamp)
            current_timestamp = response.get(CURRENT_DATE)
            homeworks = check_response(response)

            if homeworks:
                message = parse_status(homeworks[0])

            if message != cached_message:
                send_message(bot=bot, message=message)
                logging.info(f'Send message {message}')
            time.sleep(RETRY_TIME)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(f'{message}')

            if not isinstance(error, telegram.error.TelegramError):
                try:
                    if message != cached_message:
                        send_message(bot=bot, message=message)
                        logging.info(f'Send message {message}')
                except Exception as error:
                    logging.error(f'Сбой в работе программы: {error}')

            time.sleep(RETRY_TIME)
        else:
            logging.debug(f'Send message {message}')
        cached_message = message


if __name__ == '__main__':
    main()
