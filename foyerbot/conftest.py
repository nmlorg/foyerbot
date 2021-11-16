"""Special runner for .transcript files."""

import difflib
import re
import shlex
import urllib

import ntelebot
import pytest

from foyerbot import __main__


class MockBot(ntelebot.bot.Bot):  # pylint: disable=missing-class-docstring

    BASE_URL = 'http://localhost'

    def __init__(self, tester):
        super().__init__('12345678:aaaabbbbcccc')
        self.__username = f"test{self.token.split(':', 1)[0]}bot"
        self.__tester = tester

    @staticmethod
    def _encode_kwargs(kwargs):
        return ' '.join(f'{k}={v}' for (k, v) in kwargs.items())

    @staticmethod
    def create_chat_invite_link(**kwargs):  # pylint: disable=missing-function-docstring
        return {'invite_link': f'https://example.com/?{urllib.parse.urlencode(kwargs)}'}

    def get_me(self):  # pylint: disable=missing-function-docstring
        return {'username': self.__username}

    def send_message(self, *, chat_id, text):  # pylint: disable=missing-function-docstring
        self.__tester.check_chat(chat_id)
        lines = text.splitlines()
        prefix = f'{self.__username}:  '
        self.__tester.actual.append(f'{prefix}{lines[0]}')
        prefix = ' ' * len(prefix)
        for line in lines[1:]:
            self.__tester.actual.append(f'{prefix}{line}')

    def __getattr__(self, key):

        def func(*, chat_id, text=None, caption=None, **kwargs):
            message = f'[{key} {self._encode_kwargs(kwargs)}]'
            if text:
                message = f'{message}\n{text}'
            if caption:
                message = f'{message}\n{caption}'
            self.send_message(chat_id=chat_id, text=message)

        return func


class TranscriptTester:  # pylint: disable=missing-class-docstring

    chatid = -1

    def __init__(self):
        self.reset()

    def reset(self):  # pylint: disable=missing-function-docstring
        self.chatid = -1
        self.people = {}
        self.expected = []
        self.actual = []
        self.bot = MockBot(self)

    def check_chat(self, chatid):
        """Add a chatid marker if the next message is to a different chat."""

        if chatid != self.chatid:
            self.chatid = chatid
            self.actual.append(f'[{chatid}]')

    def handle(self, line, update):
        """Record a parsed transcript line, then run it through the bot's top-level handler."""

        assert len(update) == 1
        message = next(iter(update.values()))
        if message.get('chat'):
            self.check_chat(message['chat']['id'])
        self.expected.append(line)
        self.actual.append(line)
        __main__.handle(self.bot, self.people, update)


def pytest_collect_file(parent, path):
    """pytest hook: Return a pytest.File subclass if the given file is a test."""

    if path.ext == '.transcript' and path.basename.startswith('test'):
        return TranscriptFile.from_parent(parent, fspath=path)


class TranscriptFile(pytest.File):
    """A .transcript file."""

    def collect(self):
        with self.fspath.open() as fobj:
            lines = fobj.read().splitlines()

        monkeypatch = pytest.MonkeyPatch()
        monkeypatch.setattr('foyerbot.phrase.generate', lambda: ('2 + 2', '4', 'Solve!'))
        monkeypatch.setattr('foyerbot.image.render', lambda text: f'[Image: {text}]')
        monkeypatch.setattr('time.time', lambda: 1e9)

        tester = TranscriptTester()
        lastcomment = ''
        chatid = -1

        def gen():
            ret = TranscriptItem.from_parent(self,
                                             name=lastcomment.rstrip('.').replace('.', '\u2024'),
                                             actual=tester.actual,
                                             expected=tester.expected)
            tester.reset()
            return ret

        for line in lines:
            if line.startswith('#'):
                lastcomment = line[1:].strip()
                continue

            if not line:
                if tester.expected:
                    yield gen()
                continue

            ret = re.search('^user([0-9]+):  (.+)$', line)
            if ret:
                userid, text = ret.groups()
                userid = int(userid)
                if text.startswith('[') and text.endswith(']'):
                    message_type, *args = shlex.split(text[1:-1])
                    message = dict(arg.split('=', 1) for arg in args)
                else:
                    message_type = 'message'
                    message = {'text': text}
                message['from'] = {'id': userid}
                message['chat'] = {'id': chatid}
                tester.handle(line, {message_type: message})
                continue

            ret = re.search(r'^\[(-?[0-9]+)\]$', line)
            if ret:
                tester.expected.append(line)
                chatid = int(ret.groups()[0])
                continue

            tester.expected.append(line)

        if tester.expected:
            yield gen()

        monkeypatch.undo()


class TranscriptItem(pytest.Item):
    """A self-contained test from a .transcript file."""

    def __init__(self, name, parent, actual, expected):
        super().__init__(name, parent)
        self.actual = actual
        self.expected = expected

    def runtest(self):
        if self.actual != self.expected:
            raise Exception(difflib.ndiff(self.expected, self.actual))

    def repr_failure(self, excinfo, style=None):
        return '\n'.join(excinfo.value.args[0])

    def reportinfo(self):
        return self.fspath, 0, self.name
