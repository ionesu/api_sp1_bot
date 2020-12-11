import logging
import os
import time

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(filename='example.log', level=logging.DEBUG)

PRAKTIKUM_TOKEN = os.getenv("PRAKTIKUM_TOKEN")
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
bot = telegram.Bot(token=TELEGRAM_TOKEN)
url_praktikum = 'https://praktikum.yandex.ru/api/user_api/'
delay_get = 300
delay_error = 5


def parse_homework_status(homework):
    homework_name = homework.get('homework_name')
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
            '\tInvalid response from the server. The server responded "{}".'.format(
                homework_status))
        return 'Wrong response from the server.'


def get_homework_statuses(current_timestamp):
    if current_timestamp is None:
        current_timestamp = int(time.time())
    headers = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
    url = '{}{}'.format(url_praktikum, 'homework_statuses/')
    try:
        homework_statuses = requests.get(url,
                                         params={
                                             'from_date': current_timestamp},
                                         headers=headers)
    except requests.exceptions.Timeout:
        logging.error("\tVery Slow Internet Connection.")
        return {}
    except requests.exceptions.ConnectionError:
        logging.error("\tNetwork Unavailable. Check your connection.")
        return {}
    except requests.exceptions.MissingSchema:
        logging.error("\t503 Service Unavailable. Retrying download ... ")
        return {}
    return homework_statuses.json()


def send_message(message):
    return bot.send_message(chat_id=CHAT_ID, text=message)


def main():
    current_timestamp = int(time.time())

    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            if new_homework.get('homeworks'):
                send_message(
                    parse_homework_status(new_homework.get('homeworks')[0]))
            current_timestamp = new_homework.get('current_date')
            time.sleep(delay_get)

        except Exception as e:
            print(f'Bot die with exception: {e}')
            time.sleep(delay_error)
            continue


if __name__ == '__main__':
    main()
