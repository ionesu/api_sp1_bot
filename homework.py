import logging
import os
import time
import json

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(filename='example.log', level=logging.DEBUG)

PRAKTIKUM_TOKEN = os.getenv("PRAKTIKUM_TOKEN")
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
BOT = telegram.Bot(token=TELEGRAM_TOKEN)
URL_PRAKTIKUM = 'https://praktikum.yandex.ru/api/user_api/'
DELAY_GET = 300
DELAY_ERROR = 5


def parse_homework_status(homework):
    homework_name = homework.get('homework_name')
    if homework_name is None:
        logging.error(
            'Invalid response from the server. The server responded "{}".'.format(
                homework_name))
        return 'Wrong response from the server.'
    answer = {'rejected': 'К сожалению в работе нашлись ошибки.',
              'approved': ('Ревьюеру всё понравилось, можно '
                           'приступать к следующему уроку.')
              }
    homework_status = homework.get('status')
    if homework_status in ('rejected', 'approved'):
        verdict = answer[homework_status]
        return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'
    else:
        logging.error(
            'Invalid response from the server. The server responded "{}".'.format(
                homework_status))
        return 'Wrong response from the server.'


def get_homework_statuses(current_timestamp):
    if current_timestamp is None:
        current_timestamp = int(time.time())
    headers = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
    url = '{}{}'.format(URL_PRAKTIKUM, 'homework_statuses/')
    try:
        homework_statuses = requests.get(url,
                                         params={
                                             'from_date': current_timestamp},
                                         headers=headers)
    except requests.exceptions.RequestException as e:
        logging.error(f'Connection crashed with an error: {e}')
        return {}
    except json.JSONDecodeError:
        logging.error(
            'The server responds, but the page returned from the site does not have json')
        return {}
    return homework_statuses.json()

def send_message(message, bot_client):
    return bot_client.send_message(chat_id=CHAT_ID, text=message)


def main():
    current_timestamp = int(time.time())

    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            if new_homework.get('homeworks'):
                send_message(parse_homework_status(new_homework.get('homeworks')[0]), BOT)
            current_timestamp = new_homework.get('current_date')
            time.sleep(DELAY_GET)

        except Exception as e:
            logging.error(f'Bot die with exception: {e}')
            time.sleep(DELAY_ERROR)
            continue


if __name__ == '__main__':
    main()
