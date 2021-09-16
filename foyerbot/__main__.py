import hmac
import logging
import pprint
import sys
import time

import ntelebot


def main(args):
    logging.basicConfig(format='%(asctime)s %(levelname)s %(filename)s:%(lineno)s] %(message)s',
                        level=logging.INFO)

    if len(args) != 2:
        print(f'Usage: {args[0]} BOT:TOKEN')
        return 1

    bot = ntelebot.bot.Bot(args[1])
    people = {}

    def Sign(s):
        return hmac.new(bot.token.encode('ascii'), s.encode('ascii'), 'sha1').hexdigest()[:8]

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
            if userid != message['chat']['id']:
                if text == '/link':
                    groupid = str(message['chat']['id'])
                    try:
                        bot.send_message(chat_id=userid,
                                         text=bot.encode_url(f'{groupid} {Sign(groupid)}'))
                    except:
                        bot.send_message(chat_id=message['chat']['id'],
                                         text='Send me a private message first!')
                continue

            userinfo = people.get(userid)
            if userinfo is None:
                people[userid] = userinfo = {}

            if text.startswith('/start '):
                text = ntelebot.deeplink.decode(text[len('/start '):])

            if userinfo.get('challenge'):
                if text != userinfo['challenge']:
                    bot.send_message(chat_id=message['chat']['id'], text='Nope!')
                    continue

                bot.send_message(chat_id=message['chat']['id'], text='Yep!')
                userinfo.pop('challenge')
                userinfo['verified'] = True
                text = userinfo.pop('initial', '')
            elif not userinfo.get('verified'):
                userinfo['initial'] = text
                userinfo['challenge'] = 'cats'
                bot.send_message(chat_id=message['chat']['id'],
                                 text='Type "cats" without the quotes.')
                continue

            if text:
                if text.count(' ') == 1:
                    groupid, sig = text.split(' ')
                    if hmac.compare_digest(Sign(groupid), sig):
                        logging.info('Trying to create link for %r.', groupid)
                        try:
                            invite_link = bot.create_chat_invite_link(
                                chat_id=groupid, expire_date=time.time() + 60 * 10, member_limit=1)
                        except:
                            logging.exception('Failed:')
                        else:
                            bot.send_message(chat_id=message['chat']['id'],
                                             text=invite_link['invite_link'])
                            continue

                bot.send_message(chat_id=message['chat']['id'], text='\U0001f50a ' + text)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
