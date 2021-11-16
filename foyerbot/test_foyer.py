"""Tests for foyerbot.foyer."""

import base64

from foyerbot import foyer

GROUPID = -1001000002000


def test_sign():
    """Verify some constants used for request signatures."""

    sig = foyer.sign('12345678:aaaabbbbcccc', str(GROUPID))
    assert sig == '292ea3ae'
    deeplink = f'/v {GROUPID} {sig}'
    assert base64.urlsafe_b64encode(
        deeplink.encode('ascii')) == b'L3YgLTEwMDEwMDAwMDIwMDAgMjkyZWEzYWU='
