import telebot
import requests
import psycopg2
import someconst

# 1. По адресу нужно понимать, что это за криптовалюта +
# 2. Возможность по адресу получать текущий баланс +
# 3. Возможность по адресу получать список транзакций +

# api for btc
# https://www.blockchain.com/ru/api

# api for eth
# https://etherscan.io/apis

# db connection
conn = psycopg2.connect(dbname=someconst.DBNAME, user=someconst.USER, password=someconst.PASSWORD, host=someconst.HOST)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS logs (
                                                    id SERIAL PRIMARY KEY,
                                                    command CHARACTER VARYING(50), 
                                                    request CHARACTER VARYING(300),
                                                    response CHARACTER VARYING(100), 
                                                    status INTEGER,
                                                    date TIMESTAMP);''')
# For working with bd on server should be table logs (
#                                                     id SERIAL PRIMARY KEY,
#                                                     command CHARACTER VARYING(50),
#                                                     request CHARACTER VARYING(300),
#                                                     response CHARACTER VARYING(100),
#                                                     status INTEGER,
#                                                     date TIMESTAMP);)
# ex: insert cursor.execute('''insert into logs (request, response, date) values ('tmp', 'tmp', now());''')

# bot connection
# enter bot's token
bot = telebot.TeleBot(someconst.BOT_TOKEN)


def is_bitcoin(address: str) -> bool:
    response = requests.get('https://blockchain.info/q/addressbalance/{}'.format(address))
    make_log('currency', 'https://blockchain.info/q/addressbalance/{}'.format(address), response.status_code,
             response.text)
    if response.status_code == 200:
        return str.isnumeric(response.text)
    else:
        return False


def is_ethereum(address: str) -> bool:
    response = requests.get(
        'https://api.etherscan.io/api?module=account&action=balance&address={}&tag=latest&apikey=0x15f8e5ea1079d9a0bb04a4c58ae5fe7654b5b2b4463375ff7ffb490aa0032f3a&apikey=0x4e9ce36e442e55ecd9025b9a6e0d88485d628a67'.format(
            address))
    make_log('currency',
             'https://api.etherscan.io/api?module=account&action=balance&address={}&tag=latest&apikey=0x15f8e5ea1079d9a0bb04a4c58ae5fe7654b5b2b4463375ff7ffb490aa0032f3a&apikey=0x4e9ce36e442e55ecd9025b9a6e0d88485d628a67'.format(
                 address),
             response.status_code,
             response.text)
    if response.status_code == 200:
        return response.json().get('message') == 'OK'
    else:
        return False


def parse_coin(string_with_coins: str, currency: str) -> int:
    if currency.lower() == 'btc' and string_with_coins.isnumeric():
        return int(string_with_coins) / 10 ** 8
    elif currency.lower() == 'eth' and string_with_coins.isnumeric():
        return int(string_with_coins) / 10 ** 18
    else:
        return -1


def make_log(command: str, request: str, status: int, response: str, ) -> None:
    cursor.execute('''insert into logs (command, request, status, response, date) values (%s, %s, %s, %s, now());''',
                   (command, request, status, response))
    conn.commit()
    

@bot.message_handler(commands=['help', 'start'])
def help_message(message):
    bot.send_message(message.chat.id, 'command list:'
                                      '\n>currency <address> for check currency'
                                      '\n>balance <address> for check balance of wallet'
                                      '\n>transactions <address> for check transactions with this wallet')


@bot.message_handler(content_types=['text'])
def send_message(message):
    try:
        command, address = message.text.split()
    except ValueError:
        bot.send_message(message.chat.id, 'wrong enter, please try again or send  me "/help" for commandList')
        return

    if command.lower() == 'currency':
        if is_bitcoin(address):
            bot.send_message(message.chat.id, 'btc')

        elif is_ethereum(address):
            bot.send_message(message.chat.id, 'eth')

        else:
            bot.send_message(message.chat.id, 'wrong address')

    elif command.lower() == 'balance':
        if is_bitcoin(address):
            response = requests.get('https://blockchain.info/q/addressbalance/{}'.format(address))
            make_log('balance', 'https://blockchain.info/q/addressbalance/{}'.format(address), response.status_code,
                     response.text)
            if response.status_code == 200:
                bot.send_message(message.chat.id, '{} BTC'.format(parse_coin(response.text, 'btc')))
            else:
                bot.send_message(message.chat.id, 'wrong response, code {}'.format(response.status_code))

        elif is_ethereum(address):
            response = requests.get(
                'https://api.etherscan.io/api?module=account&action=balance&address={}&tag=latest&apikey=0x15f8e5ea1079d9a0bb04a4c58ae5fe7654b5b2b4463375ff7ffb490aa0032f3a&apikey=0x4e9ce36e442e55ecd9025b9a6e0d88485d628a67'.format(
                    address))
            make_log('balance',
                     'https://api.etherscan.io/api?module=account&action=balance&address={}&tag=latest&apikey=0x15f8e5ea1079d9a0bb04a4c58ae5fe7654b5b2b4463375ff7ffb490aa0032f3a&apikey=0x4e9ce36e442e55ecd9025b9a6e0d88485d628a67'.format(
                         address),
                     response.status_code,
                     response.json().get('result'))
            if response.status_code == 200:
                bot.send_message(message.chat.id, '{} ETH'.format(parse_coin(response.json().get('result'), 'eth')))
            else:
                bot.send_message(message.chat.id, "wrong response, code {}".format(response.status_code))

        else:
            bot.send_message(message.chat.id, 'wrong address')

    elif command == 'transactions':
        if is_bitcoin(address):
            response = requests.get('https://blockchain.info/rawaddr/{}'.format(address))
            make_log('transactions',
                     'https://blockchain.info/rawaddr/{}'.format(address),
                     response.status_code,
                     str(len(response.json().get('txs'))))
            if response.status_code == 200:
                transactions = response.json().get('txs')
                for transaction in transactions:
                    for i in transaction.get('out'):
                        bot.send_message(message.chat.id,
                                         'from this wallet to {0} \nvalue {1} BTC'.format(i['addr'],
                                                                                          parse_coin(str(i['value']),
                                                                                                     'btc')))
            else:
                bot.send_message(message.chat.id, "wrong response, code {}".format(response.status_code))

        elif is_ethereum(address):
            response = requests.get(
                'http://api.etherscan.io/api?module=account&action=txlist&address={}&startblock=0&endblock=99999999&sort=asc&apikey=YourApiKeyToken'.format(
                    address))
            make_log('transaction',
                     'http://api.etherscan.io/api?module=account&action=txlist&address={}&startblock=0&endblock=99999999&sort=asc&apikey=YourApiKeyToken'.format(
                         address),
                     response.status_code,
                     str(len(response.json().get('result'))))
            if response.status_code == 200:
                for transaction in response.json().get('result'):
                    bot.send_message(message.chat.id,
                                     'from {0} \nto {1} \nvalue {2} ETH'.format(transaction.get('from'),
                                                                                transaction.get('to'),
                                                                                parse_coin(transaction.get('value'),
                                                                                           'eth')))
            else:
                bot.send_message(message.chat.id, 'wrong response, code {}'.format(response.status_code))

        else:
            bot.send_message(message.chat.id, "wrong address")


bot.polling()
