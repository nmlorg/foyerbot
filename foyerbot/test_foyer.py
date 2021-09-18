import base64

import ntelebot
import pytest

from foyerbot import foyer


class MockBot(ntelebot.bot.Bot):

    BASE_URL = 'http://localhost'

    def __init__(self, tester):
        super().__init__('12345678:aaaabbbbcccc')
        self.__tester = tester

    @staticmethod
    def _encode_kwargs(kwargs):
        return ' '.join(f'{k}={v}' for (k, v) in kwargs.items())

    def create_chat_invite_link(self, **kwargs):
        return {'invite_link': f'https://example.com/{self._encode_kwargs(kwargs)}'}

    def get_me(self):
        return {'username': 'foyertestbot'}

    def __getattr__(self, key):

        def func(text=None, **kwargs):
            self.__tester.actions.append('')
            self.__tester.actions.append(f'[{key} {self._encode_kwargs(kwargs)}]')
            if text:
                self.__tester.actions.append(text)
                self.__tester.actions.append('')

        return func


class FoyerTester:

    def __init__(self):
        self.people = {}
        self.actions = []
        self.bot = MockBot(self)

    def handle(self, userid, chatid, text):
        self.actions.clear()
        foyer.handle(self.bot, self.people, userid, chatid, text)
        return '\n'.join(self.actions)


@pytest.fixture(name='tester')
def _tester():
    return FoyerTester()


USERID = 1000
GROUPID = -1001000002000


def test_sign(tester):
    sig = foyer.sign(tester.bot.token, str(GROUPID))
    assert sig == '292ea3ae'
    deeplink = f'{GROUPID} {sig}'
    assert base64.urlsafe_b64encode(deeplink.encode('ascii')) == b'LTEwMDEwMDAwMDIwMDAgMjkyZWEzYWU='


def test_link(tester):
    assert tester.handle(USERID, GROUPID, '/dummy') == ''
    assert tester.handle(USERID, GROUPID, '/link') == """
[send_message chat_id=1000]
https://t.me/foyertestbot?start=LTEwMDEwMDAwMDIwMDAgMjkyZWEzYWU
"""


def test_request(monkeypatch, tester):
    assert tester.handle(USERID, USERID, '/start LTEwMDEwMDAwMDIwMDAgMjkyZWEzYWU') == """
[send_message chat_id=1000]
Type "cats" without the quotes.
"""
    assert tester.people == {1000: {'challenge': 'cats', 'initial': '-1001000002000 292ea3ae'}}

    assert tester.handle(USERID, USERID, 'robots') == """
[send_message chat_id=1000]
Nope!
"""
    assert tester.people == {1000: {'challenge': 'cats', 'initial': '-1001000002000 292ea3ae'}}

    monkeypatch.setattr('time.time', lambda: 1e9)

    assert tester.handle(USERID, USERID, 'cats') == """
[send_message chat_id=1000]
Yep!


[send_message chat_id=1000]
https://example.com/chat_id=-1001000002000 expire_date=1000000600.0 member_limit=1
"""
    assert tester.people == {1000: {'verified': True}}


def test_unknown(tester):
    assert tester.handle(USERID, USERID, 'robots') == """
[send_message chat_id=1000]
Type "cats" without the quotes.
"""

    assert tester.handle(USERID, USERID, 'cats') == """
[send_message chat_id=1000]
Yep!


[send_message chat_id=1000]
🔊 robots
"""

    assert tester.handle(USERID, USERID, 'spaceships') == """
[send_message chat_id=1000]
🔊 spaceships
"""
