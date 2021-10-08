"""Tests for foyerbot.freqtable."""

from foyerbot import freqtable


def test_simple(monkeypatch):
    """Verify FrequencyTable's basic behavior."""

    ftab = freqtable.FrequencyTable(3)
    assert ftab == []

    now = 100
    monkeypatch.setattr('time.time', lambda: now)

    ftab.update({'alpha', 'bravo'})
    assert ftab == [[0, 100, 'bravo'], [0, 100, 'alpha']]

    now = 200
    ftab.update({'bravo', 'charlie'})
    assert ftab == [[1, 200, 'bravo'], [0, 200, 'charlie'], [0, 100, 'alpha']]

    now = 300
    ftab.update({'alpha', 'bravo'})
    assert ftab == [[2, 300, 'bravo'], [1, 300, 'alpha'], [0, 200, 'charlie']]

    # Adding a new entry forces the lowest entry to fall off.
    now = 400
    ftab.update({'delta'})
    assert ftab == [[2, 300, 'bravo'], [1, 300, 'alpha'], [0, 400, 'delta']]

    # ... even if the lowest entry isn't necessarily equal to the new entry.
    for now in range(500, 510):
        ftab.update({'alpha', 'bravo', 'delta'})
    assert ftab == [[3, 509, 'bravo'], [2, 509, 'alpha'], [1, 509, 'delta']]

    now = 600
    ftab.update({'echo'})
    assert ftab == [[2, 509, 'bravo'], [1, 509, 'alpha'], [0, 600, 'echo']]

    now = 700
    ftab.update({'foxtrot'})
    assert ftab == [[2, 509, 'bravo'], [1, 509, 'alpha'], [0, 700, 'foxtrot']]
