from __future__ import annotations

import logging
import os
import sys
import time
from http import HTTPStatus
from typing import Any, Dict, Optional, TypeVar

import requests
import telegram
from dotenv import load_dotenv
from telegram import Bot

from exceptions import PracticumAPIError

load_dotenv()

JSONType = Dict[str, Any]
T = TypeVar('T')


def cast_away_optional(arg: Optional[T]) -> T:
    """Allows cast away optional type `None` from `arg`."""
    assert arg is not None
    return arg


def cast_int_type(arg: Any) -> int:
    """Casts type `int` for `arg`."""
    assert isinstance(arg, int)
    return arg


PRACTICUM_TOKEN: Optional[str] = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN: Optional[str] = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID: Optional[str] = os.getenv('TELEGRAM_CHAT_ID')

ENDPOINT: str = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS: dict[str, str] = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
RETRY_TIME: int = 600

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


def set_logger() -> None:
    """Set configuration of the root logger."""
    handlers = (logging.StreamHandler(stream=sys.stdout), )
    logging.basicConfig(
        format='%(asctime)s [%(levelname)s] %(message)s',
        level=logging.DEBUG,
        handlers=handlers
    )


def send_message(bot: Bot, message: str) -> None:
    """Sends message from a telegram bot to a telegram chat."""
    try:
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message
        )
    except telegram.error.TelegramError as e:
        logging.error(f'Problem with the program: {e}')
    else:
        logging.info(f'Send message {message}')


def get_api_answer(current_timestamp: Optional[float] = None) -> JSONType:
    """Gets json response from the API and transforms it to python types."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}

    response = requests.get(
        url=ENDPOINT,
        headers=HEADERS,
        params=params
    )
    if response.status_code != HTTPStatus.OK:
        response.raise_for_status()
    info: JSONType = response.json()
    return info


def check_response(response: JSONType) -> list[JSONType]:
    """Validates the structure of the response from the API."""
    try:
        homeworks: list[JSONType] = response[HOMEWORKS]
        _ = response[CURRENT_DATE]
    except TypeError as e:
        raise TypeError(f'{e} - "{response}" is not a {JSONType} type')
    except KeyError as e:
        raise PracticumAPIError(f'There is no "{e}" key in API response')

    if isinstance(homeworks, list):
        return homeworks
    else:
        raise PracticumAPIError(
            f'{type(homeworks)} is not `list` type value'
        )


def parse_status(homework: JSONType) -> str:
    """Returns message about a homework review status."""
    try:
        homework_name = homework[HOMEWORK_NAME]
        homework_status = homework[STATUS]
    except KeyError as e:
        raise type(e)(f'There is no {e} key in the API response')

    try:
        verdict = HOMEWORK_STATUSES[homework_status]
    except KeyError as e:
        raise type(e)(f'There is no {e} in {HOMEWORK_STATUSES}')

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens() -> bool:
    """Checks for presence of all required variables from the environment."""
    tokens = {
        'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
        'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID,
        'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
    }
    for name, token in tokens.items():
        if not token:
            logging.critical(
                f'Missing required environment variable `{name}`'
            )
            return False
    return True


def main() -> None:
    """Main logic of bot working."""
    if not check_tokens():
        sys.exit(0)

    bot = telegram.Bot(token=cast_away_optional(TELEGRAM_TOKEN))
    current_timestamp = int(time.time())

    cached_message: Optional[str] = None
    message: Optional[str] = None
    while True:
        try:
            response = get_api_answer(current_timestamp=current_timestamp)
            current_timestamp = cast_int_type(response.get(CURRENT_DATE))
            homeworks = check_response(response)

            if homeworks:
                message = parse_status(homeworks[0])

            if message != cached_message:
                send_message(bot=bot, message=cast_away_optional(message))

        except Exception as error:
            message = f'Problem with the program: {error}'
            logging.error(f'{message}')

            if message != cached_message:
                send_message(bot=bot, message=message)

        else:
            logging.debug(f'Current `message` is "{message}"')

        cached_message = message
        time.sleep(RETRY_TIME)


if __name__ == '__main__':
    set_logger()
    main()
