"""List of recently seen strings, sorted by decreasing frequency and age."""

import time


class FrequencyTable(list):
    """List of recently seen strings, sorted by decreasing frequency and age."""

    def __init__(self, size, initial=()):
        super().__init__(initial)
        self.size = size

    def update(self, entries):
        """Add/update a container of 1 or more strings."""

        if len(self) >= self.size and self[-1][0]:
            lowest_count = self[-1][0]
            for row in self:
                row[0] -= lowest_count

        entries = set(entries)
        now = int(time.time())
        for row in self:
            entry = row[2]
            if entry in entries:
                row[0] += 1
                row[1] = now
                entries.remove(entry)
                if not entries:
                    break

        for entry in entries:
            self.append([0, now, entry])

        self.sort(reverse=True)
        while len(self) > self.size:
            self.pop(-1)
