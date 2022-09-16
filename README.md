# homework_bot

<a href="https://docs.python.org/3.7/">
<img src="https://img.shields.io/badge/Python-3.7-FFE873.svg?labelColor=4B8BBE" 
alt="Python requirement">
</a>

<a>
<img src="https://img.shields.io/badge/Tests-passing-32CD32.svg?labelColor=555">
</a>

<a href="https://flake8.pycqa.org/en/3.9/">
<img src="https://img.shields.io/badge/flake8-4.0.1-E4D00A.svg?labelColor=555">
</a>

<a href="https://mypy.readthedocs.io/en/stable/">
<img src="https://img.shields.io/badge/mypy-0.961-E4D00A.svg?labelColor=555">
</a>

<a href="https://docs.pytest.org/en/6.2.x/contents.html">
<img src="https://img.shields.io/badge/pytest-6.2-E4D00A.svg?labelColor=555">
</a>

## About

A service that notifies about your homework status in 
[YandexPracticum](https://yandex.ru/support/praktikum/) 
using YandexPracticum.Homework API: 
* polls the service API and checks the status of the submitted homework;
* sends notifications to your Telegram using Telegram bot in case of 
  homework status update;
* logs its work and informs you about important problems with a message in 
  Telegram.

Tech stack: \
[python-telegram-bot](https://docs.python-telegram-bot.org/en/v13.7/),
[requests](https://requests.readthedocs.io/en/stable/)

## Application

Before running the main `homework.py` script, create a `.env` file and set the
secrete keys. Use the `example_env` file as an example.
