"""Create a hard-to-read phrase made of real English words."""

import random

from foyerbot import words

LEET = {
    'a': ('@', '4', '\u03b1'),
    'b': ('6', '8', '\u03b2'),
    'c': ('\xa9', '\xa2'),
    'e': ('3', '\u03b5'),
    'g': ('q', '9'),
    'i': ('1', '!'),
    'l': ('|',),
    'o': ('0',),
    'q': ('g',),
    'r': ('\xae',),
    's': ('$', '5'),
    't': ('+',),
    'z': ('2',),
}


def _leetify(text):
    ret = []
    for letter in text:
        choices = (letter, letter.upper())
        if letter in LEET:
            choices += LEET[letter]
        ret.append(random.choice(choices))
    return ''.join(ret)


def generate():
    """Create a hard-to-read phrase made of real English words."""

    num = 3
    answer = ' '.join(words.sample(num))
    return _leetify(answer), answer, f'Type the {num} English words.'
