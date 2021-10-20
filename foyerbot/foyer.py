"""Simple bot to provide Telegram group invite links to users after solving a challenge."""

import hmac
import logging
import re
import time

import ntelebot

from foyerbot import image
from foyerbot import phrase
from foyerbot import words


class _Step:

    def handle(self, bot, userid, text):
        """Handle a message from userid to bot containing text."""


class _TextPrompt(_Step):

    def __init__(self, prompt, expect):
        self.prompt = prompt
        self.expect = expect

    def handle(self, bot, userid, text):
        if self.satisfied(text):
            return True

        self.send(bot, userid)

    def satisfied(self, text):
        """Does text satisfy this step?"""

        return text.casefold() == self.expect.casefold()

    def send(self, bot, userid):
        """Send this step's prompt to userid via bot."""

        bot.send_message(chat_id=userid, text=self.prompt)


class _RegexPrompt(_TextPrompt):

    def satisfied(self, text):
        return bool(re.search(self.expect, text))


class _Captcha(_TextPrompt):
    sent_image = False

    def __init__(self):
        self.question, expect, prompt = phrase.generate()
        super().__init__(prompt, expect)

    def send(self, bot, userid):
        if not self.sent_image:
            self.sent_image = True
            img = image.render(self.question)
            logging.info('Sending %r (%s); expecting %r.', self.question, self.prompt, self.expect)
            bot.send_photo(chat_id=userid, photo=img, caption=self.prompt)
        else:
            super().send(bot, userid)


class _InviteLink(_Step):

    def __init__(self, groupid):
        self.groupid = groupid

    def handle(self, bot, userid, text):
        logging.info('Trying to create link for %r.', self.groupid)
        try:
            info = bot.create_chat_invite_link(chat_id=self.groupid,
                                               expire_date=int(time.time()) + 60 * 10,
                                               member_limit=1)
        except ntelebot.errors.Forbidden:
            logging.exception('Failed:')
            bot.send_message(
                chat_id=userid,
                text=f"Sorry, something went wrong trying to generate a link for {self.groupid}.")
        else:
            bot.send_message(chat_id=userid, text=info['invite_link'])
        return True


def sign(key, text):
    """Generate a hex-encoded HMAC-SHA1-32(key, text)."""

    return hmac.new(key.encode('ascii'), text.encode('ascii'), 'sha1').hexdigest()[:8]


def handle(bot, people, userid, chatid, text):
    """Handle a message sent to bot from userid in chatid containing text."""

    if userid != chatid:
        return group(bot, userid, chatid, text)

    return private(bot, people, userid, text)


def group(bot, userid, chatid, text):
    """Handle a message sent to a group chat."""

    if text == '/link':
        chatidstr = str(chatid)
        try:
            bot.send_message(chat_id=userid,
                             text=bot.encode_url(f'/v {chatidstr} {sign(bot.token, chatidstr)}'))
        except ntelebot.errors.Forbidden:
            logging.exception('Failed:')
            bot.send_message(chat_id=chatid, text='Send me a private message first!')
    else:
        words.learn(text)


def private(bot, people, userid, text):
    """Handle a private message."""

    userinfo = people.get(userid)
    if userinfo is None:
        people[userid] = userinfo = {}

    if text.startswith('/start '):
        text = ntelebot.deeplink.decode(text[len('/start '):])

    if text.startswith('/v ') and text.count(' ') == 2:
        _, groupid, sig = text.split(' ')
        text = ''
        if not hmac.compare_digest(sign(bot.token, groupid), sig):
            return bot.send_message(chat_id=userid, text="Sorry, that code isn't right.")

        userinfo['steps'] = [_Captcha(), _InviteLink(groupid)]

    steps = userinfo.get('steps')

    while steps:
        step = steps[0]
        if not step.handle(bot, userid, text):
            return
        steps.pop(0)
        text = ''

    if text:
        bot.send_message(chat_id=userid, text='\U0001f50a ' + text)
