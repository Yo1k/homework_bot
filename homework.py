from __future__ import annotations
import os
import sys
import time
from pprint import pprint
from typing import Optional, Any
import urllib.request

import telegram
from dotenv import load_dotenv
import requests
from telegram import Bot

load_dotenv()

JSONType = dict[str, Any] # SKTODO use TypedDict

PRACTICUM_TOKEN: Optional[str] = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN: Optional[str] = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID: Optional[str] = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME: int = 10 # SKTODO set value 600
ENDPOINT: str = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS: dict[str, str] = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

# Keys of the response of the ENDPOINT API:
HOMEWORKS: str = 'homeworks'
CURRENT_DATE: str = 'current_date'
# Keys in an element in `HOMEWORKS` array:
HOMEWORK_NAME: str = 'homework_name'
STATUS: str = 'status'

HOMEWORK_STATUSES: dict[str, str] = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


class UnsetEnvVarException(Exception):
    pass


class PracticumAPIError(Exception):
    pass


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
    if (
            PRACTICUM_TOKEN
            and TELEGRAM_TOKEN
            and TELEGRAM_CHAT_ID
    ):
        return True
    else:
        return False


def main() -> None:
    """Основная логика работы бота."""

    if not check_tokens():
        raise UnsetEnvVarException('Not all environment variables are set')

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = 1 #int(time.time())

    message_cache: Optional[str] = None
    message: Optional[str] = None
    while True:
        try:
            response = get_api_answer(current_timestamp=current_timestamp)
            current_timestamp = response.get(CURRENT_DATE)
            homeworks = check_response(response)

            if homeworks:
                message = parse_status(homeworks[0])

            if message != message_cache:
                send_message(bot=bot, message=message)
            time.sleep(RETRY_TIME)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            if not isinstance(error, telegram.error.TelegramError):
                try:
                    if message != message_cache:
                        send_message(bot=bot, message=message)
                except Exception as error:
                    raise type(error)(f'Сбой в работе программы: {error}')
            time.sleep(RETRY_TIME)
        else:
            pass # SKTODO logging INFO: send message
        message_cache = message


if __name__ == '__main__':
    main()
