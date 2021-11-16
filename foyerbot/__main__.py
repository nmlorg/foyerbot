"""Simple bot to provide Telegram group invite links to users after solving a challenge."""

import argparse
import logging
import pprint

import ntelebot

from foyerbot import foyer


def handle(bot, people, update):  # pylint: disable=missing-function-docstring
    logging.info('\n%s', pprint.pformat(update))

    chat_join_request = update.get('chat_join_request')
    if chat_join_request:
        if not chat_join_request.get('from') or not chat_join_request.get('chat'):
            return
        userid = chat_join_request['from']['id']
        chatid = chat_join_request['chat']['id']

        foyer.chat_join_request(bot, people, userid, chatid)
        return

    message = update.get('message')
    if message:
        if not message.get('text') or not message.get('from') or not message.get('chat'):
            return
        text = message['text']
        userid = message['from']['id']
        chatid = message['chat']['id']

        if userid != chatid:
            foyer.group(bot, userid, chatid, text)
        else:
            foyer.private(bot, people, userid, text)


def main():  # pylint: disable=missing-function-docstring
    parser = argparse.ArgumentParser()
    parser.add_argument('token')
    args = parser.parse_args()

    logging.basicConfig(format='%(asctime)s %(levelname)s %(filename)s:%(lineno)s] %(message)s',
                        level=logging.INFO)

    bot = ntelebot.bot.Bot(args.token)
    people = {}

    offset = None
    while True:
        updates = bot.get_updates(offset=offset, timeout=10)
        if not updates:
            continue

        offset = updates[-1]['update_id'] + 1
        for update in updates:
            handle(bot, people, update)


if __name__ == '__main__':
    main()
