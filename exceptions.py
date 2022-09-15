"""This module contains all specific exceptions to `homework_bot` python
package.
"""


class BotBaseException(Exception):
    """Base exception for all exceptions to `homework_bot` python package."""
    pass


class PracticumAPIError(BotBaseException):
    """An invalid API of the Practicum.Homework used."""
    pass
