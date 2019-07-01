import telebot
import requests
import psycopg2
import hmac

# db connection
conn = psycopg2.connect(dbname='postgres', user='postgres', password='4556', host='localhost')
cursor = conn.cursor()
# For working with bd on server should be table logs( id SERIAL PRIMARY KEY,
#                                                     request CHARACTER VARYING(50),
#                                                     response CHARACTER VARYING(50),
#                                                     date TIMESTAMP)
# ex: insert cursor.execute('''insert into logs (request, response, date) values ('tmp', 'tmp', now());''')

# bot connection
# enter bot's token
bot = telebot.TeleBot('880750397:AAEJs4lqzwjjyuTR1RUVVMdjkVQXwCZpO98')


# todo status code checker and cash for balance and trades operation
def is_bitcoin(address: str) -> bool:
    response = requests.get('https://blockchain.info/q/addressbalance/{}'.format(address))
    if response.status_code == 200:
        return str.isnumeric(response.text)
    else:
        return False


def is_ethereum(address: str) -> bool:
    response = requests.get(
        'https://api.etherscan.io/api?module=account&action=balance&address={}&tag=latest&apikey=0x15f8e5ea1079d9a0bb04a4c58ae5fe7654b5b2b4463375ff7ffb490aa0032f3a&apikey=0x4e9ce36e442e55ecd9025b9a6e0d88485d628a67'.format(
            address))
    if response.status_code == 200:
        return response.json().get('message') == 'OK'
    else:
        return False


def make_log(request: str, response: str) -> None:
    cursor.execute('''insert into logs (request, response, date) values (%s, %s, now());''', (request, response))
    conn.commit()


@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, "Hello, i'm Viki")


@bot.message_handler(commands=['help'])
def start_message(message):
    bot.send_message(message.chat.id, 'command list:'
                                      '\nwallet <address> for check currency'
                                      '\nbalance <address> for check balance of wallet'
                                      '\ntransactions <address> for check transactions with this wallet')


@bot.message_handler(content_types=['text'])
def send_message(message):
    try:
        command, address = message.text.split()
    except ValueError:
        bot.send_message(message.chat.id, 'wrong enter, please try again or send  me "/help" for commandList')
        return

    if command.lower() == 'wallet':
        if is_bitcoin(address):
            bot.send_message(message.chat.id, 'btc')
        elif is_ethereum(address):
            bot.send_message(message.chat.id, 'eth')
        else:
            bot.send_message(message.chat.id, 'wrong address')

    elif command.lower() == 'balance':
        if is_bitcoin(address):
            response = requests.get('https://blockchain.info/q/addressbalance/{}'.format(address))
            if response.status_code == 200:
                make_log('bal {}'.format(address), response.text)
                bot.send_message(message.chat.id, response.text)
            else:
                bot.send_message(message.chat.id, "wrong response, code {}".format(response.status_code))
        elif is_ethereum(address):
            response = requests.get(
                'https://api.etherscan.io/api?module=account&action=balance&address={}&tag=latest&apikey=0x15f8e5ea1079d9a0bb04a4c58ae5fe7654b5b2b4463375ff7ffb490aa0032f3a&apikey=0x4e9ce36e442e55ecd9025b9a6e0d88485d628a67'.format(
                    address))
            if response.status_code == 200:
                make_log('bal {}'.format(address), response.json().get('result'))
                bot.send_message(message.chat.id, response.json().get('result'))
            else:
                bot.send_message(message.chat.id, "wrong response, code {}".format(response.status_code))
        else:
            bot.send_message(message.chat.id, "wrong address")  # todo something with withs cod-repeat

    elif command == 'transactions':
        pass  # todo


bot.polling()
# 1. По адресу нужно понимать, что это за криптовалюта
# 2. Возможность по адресу получать текущий баланс
# 3. Возможность по адресу получать список транзакций

# https://www.kraken.com/features/api#public-market-data
# api for btc
