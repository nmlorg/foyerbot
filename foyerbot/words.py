"""Manage lists of words to use for generating challenges."""

import os
import random
import re

from foyerbot import freqtable

_FNAME = os.path.join(os.path.dirname(__file__), 'phrases.txt')


def _load_phrases():
    try:
        with open(_FNAME, encoding='utf8') as fobj:
            phrases = [line.split(None, 2) for line in fobj.read().splitlines()]
            for row in phrases:
                row[0] = int(row[0])
                row[1] = int(row[1])
    except FileNotFoundError:
        phrases = [[0, 0, 'initial foyer phrase']]

    return phrases


PHRASES = freqtable.FrequencyTable(1000, _load_phrases())


def _save_phrases():
    with open(_FNAME, 'w', encoding='utf8') as fobj:
        for row in PHRASES:
            fobj.write(f'{row[0]} {row[1]} {row[2]}\n')


def learn(text):
    """Break text apart and add short phrases to the bot's phrase list."""

    words = [word.lower() for word in re.split(r'\W+', text) if word]
    phrases = set()
    for i in range(len(words) - 2):
        subwords = words[i:i + 3]
        if min(map(len, subwords)) < 5:
            continue
        phrase = ' '.join(subwords)
        if len(phrase) < 9 * 3:
            phrases.add(phrase)
    if not phrases:
        return

    PHRASES.update(phrases)
    _save_phrases()


def choose():
    """Return a phrase the list."""

    return random.choice(PHRASES)[2]
