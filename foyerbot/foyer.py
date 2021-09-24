"""Simple bot to provide Telegram group invite links to users after solving a challenge."""

import hmac
import logging
import time

import ntelebot


def sign(key, text):
    """Generate a hex-encoded HMAC-SHA1-32(key, text)."""

    return hmac.new(key.encode('ascii'), text.encode('ascii'), 'sha1').hexdigest()[:8]


def handle(bot, people, userid, chatid, text):  # pylint: disable=too-many-branches
    """Handle a message sent to bot from userid in chatid containing text."""

    if userid != chatid:
        if text == '/link':
            chatidstr = str(chatid)
            try:
                bot.send_message(chat_id=userid,
                                 text=bot.encode_url(f'{chatidstr} {sign(bot.token, chatidstr)}'))
            except ntelebot.errors.Forbidden:
                logging.exception('Failed:')
                bot.send_message(chat_id=chatid, text='Send me a private message first!')
        return

    userinfo = people.get(userid)
    if userinfo is None:
        people[userid] = userinfo = {}

    if text.startswith('/start '):
        text = ntelebot.deeplink.decode(text[len('/start '):])

    if userinfo.get('challenge'):
        if text != userinfo['challenge']:
            bot.send_message(chat_id=chatid, text='Nope!')
            return

        bot.send_message(chat_id=chatid, text='Yep!')
        userinfo.pop('challenge')
        userinfo['verified'] = True
        text = userinfo.pop('initial', '')
    elif not userinfo.get('verified'):
        userinfo['initial'] = text
        userinfo['challenge'] = 'cats'
        bot.send_message(chat_id=chatid, text='Type "cats" without the quotes.')
        return

    if text:
        if text.count(' ') == 1:
            chatidstr, sig = text.split(' ')
            if hmac.compare_digest(sign(bot.token, chatidstr), sig):
                logging.info('Trying to create link for %r.', chatidstr)
                try:
                    info = bot.create_chat_invite_link(chat_id=chatidstr,
                                                       expire_date=int(time.time()) + 60 * 10,
                                                       member_limit=1)
                except ntelebot.errors.Forbidden:
                    logging.exception('Failed:')
                else:
                    bot.send_message(chat_id=chatid, text=info['invite_link'])
                    return

        bot.send_message(chat_id=chatid, text='\U0001f50a ' + text)
