import logging
import pprint
import sys

import ntelebot

from foyerbot import foyer


def main(args):
    logging.basicConfig(format='%(asctime)s %(levelname)s %(filename)s:%(lineno)s] %(message)s',
                        level=logging.INFO)

    if len(args) != 2:
        print(f'Usage: {args[0]} BOT:TOKEN')
        return 1

    bot = ntelebot.bot.Bot(args[1])
    people = {}

    offset = None
    while True:
        updates = bot.get_updates(offset=offset, timeout=10)
        if not updates:
            continue

        offset = updates[-1]['update_id'] + 1
        for update in updates:
            pprint.pprint(update)
            if not update.get('message'):
                continue
            message = update['message']
            if not message.get('text') or not message.get('from') or not message.get('chat'):
                continue
            text = message['text']
            userid = message['from']['id']
            chatid = message['chat']['id']

            foyer.handle(bot, people, userid, chatid, text)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
