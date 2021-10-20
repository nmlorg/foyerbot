"""Tests for foyerbot.foyer."""

import base64

import ntelebot
import pytest

from foyerbot import foyer


class MockBot(ntelebot.bot.Bot):  # pylint: disable=missing-class-docstring

    BASE_URL = 'http://localhost'

    def __init__(self, tester):
        super().__init__('12345678:aaaabbbbcccc')
        self.__tester = tester

    @staticmethod
    def _encode_kwargs(kwargs):
        return ' '.join(f'{k}={v}' for (k, v) in kwargs.items())

    def create_chat_invite_link(self, **kwargs):  # pylint: disable=missing-function-docstring
        return {'invite_link': f'https://example.com/{self._encode_kwargs(kwargs)}'}

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

    def handle(self, userid, chatid, text):
        """Call foyer.handle() and capture and return all calls made to bot's methods."""

        self.actions.clear()
        foyer.handle(self.bot, self.people, userid, chatid, text)
        return '\n'.join(self.actions)


@pytest.fixture(name='tester')
def _tester(monkeypatch):
    monkeypatch.setattr('foyerbot.phrase.generate', lambda: ('2 + 2', '4', 'Solve!'))
    monkeypatch.setattr('foyerbot.image.render', lambda text: f'[Image: {text}]')

    return FoyerTester()


USERID = 1000
GROUPID = -1001000002000


def test_sign(tester):
    """Verify some constants used for request signatures."""

    sig = foyer.sign(tester.bot.token, str(GROUPID))
    assert sig == '292ea3ae'
    deeplink = f'/v {GROUPID} {sig}'
    assert base64.urlsafe_b64encode(
        deeplink.encode('ascii')) == b'L3YgLTEwMDEwMDAwMDIwMDAgMjkyZWEzYWU='


def test_link(tester):
    """Simulate a user typing /link in a group chat."""

    assert tester.handle(USERID, GROUPID, '/dummy') == ''
    assert tester.handle(USERID, GROUPID, '/link') == """
[send_message chat_id=1000]
https://t.me/test12345678bot?start=L3YgLTEwMDEwMDAwMDIwMDAgMjkyZWEzYWU
"""


def test_request(monkeypatch, tester):
    """Simulate a well-formed request (including verification)."""

    assert tester.handle(USERID, USERID, '/start L3YgLTEwMDEwMDAwMDIwMDAgMjkyZWEzYWU') == """
[send_photo chat_id=1000 photo=[Image: 2 + 2]]
Solve!
"""

    assert tester.handle(USERID, USERID, 'robots') == """
[send_message chat_id=1000]
Solve!
"""

    monkeypatch.setattr('time.time', lambda: 1e9)

    assert tester.handle(USERID, USERID, '4') == """
[send_message chat_id=1000]
https://example.com/chat_id=-1001000002000 expire_date=1000000600 member_limit=1
"""


def test_unknown(tester):
    """Verify the bot just echos unexpected messages."""

    assert tester.handle(USERID, USERID, 'spaceships') == """
[send_message chat_id=1000]
🔊 spaceships
"""
