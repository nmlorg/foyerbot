"""Tests for foyerbot.foyer."""

import base64
import urllib

import ntelebot

from foyerbot import foyer


class MockBot(ntelebot.bot.Bot):  # pylint: disable=missing-class-docstring

    BASE_URL = 'http://localhost'

    def __init__(self, tester):
        super().__init__('12345678:aaaabbbbcccc')
        self.__tester = tester

    @staticmethod
    def _encode_kwargs(kwargs):
        return ' '.join(f'{k}={v}' for (k, v) in kwargs.items())

    @staticmethod
    def create_chat_invite_link(**kwargs):  # pylint: disable=missing-function-docstring
        return {'invite_link': f'https://example.com/?{urllib.parse.urlencode(kwargs)}'}

    def get_me(self):  # pylint: disable=missing-function-docstring
        return {'username': f"test{self.token.split(':', 1)[0]}bot"}

    def __getattr__(self, key):

        def func(text=None, caption=None, **kwargs):
            self.__tester.actions.append('')
            self.__tester.actions.append(f'[{key} {self._encode_kwargs(kwargs)}]')
            if text:
                self.__tester.actions.append(text)
                self.__tester.actions.append('')
            if caption:
                self.__tester.actions.append(caption)
                self.__tester.actions.append('')

        return func


class FoyerTester:  # pylint: disable=missing-class-docstring,too-few-public-methods

    def __init__(self):
        self.people = {}
        self.actions = []
        self.bot = MockBot(self)

    def private(self, userid, text):
        """Call foyer.private() and capture and return all calls made to bot's methods."""

        self.actions.clear()
        foyer.private(self.bot, self.people, userid, text)
        return '\n'.join(self.actions)


USERID = 1000
GROUPID = -1001000002000


def test_sign():
    """Verify some constants used for request signatures."""

    sig = foyer.sign(FoyerTester().bot.token, str(GROUPID))
    assert sig == '292ea3ae'
    deeplink = f'/v {GROUPID} {sig}'
    assert base64.urlsafe_b64encode(
        deeplink.encode('ascii')) == b'L3YgLTEwMDEwMDAwMDIwMDAgMjkyZWEzYWU='


def test_request(monkeypatch):
    """Simulate a well-formed request (including verification)."""

    tester = FoyerTester()

    monkeypatch.setattr('foyerbot.phrase.generate', lambda: ('2 + 2', '4', 'Solve!'))
    monkeypatch.setattr('foyerbot.image.render', lambda text: f'[Image: {text}]')

    assert tester.private(USERID, '/start L3YgLTEwMDEwMDAwMDIwMDAgMjkyZWEzYWU') == """
[send_photo chat_id=1000 photo=[Image: 2 + 2]]
Solve!
"""

    assert tester.private(USERID, 'robots') == """
[send_message chat_id=1000]
Solve!
"""

    monkeypatch.setattr('time.time', lambda: 1e9)

    assert tester.private(USERID, '4') == """
[send_message chat_id=1000]
https://example.com/?chat_id=-1001000002000&expire_date=1000000600&member_limit=1
"""
