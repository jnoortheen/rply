from __future__ import annotations

from collections.abc import MutableMapping
from typing import Any, Iterator

from rply.grammar import LRItem


class IdentityDict(MutableMapping):
    def __init__(self) -> None:
        self._contents = {}
        self._keepalive = []

    def __getitem__(self, key: list[LRItem] | str | LRItem) -> Any:
        return self._contents[id(key)][1]

    def __setitem__(
        self, key: int | list[LRItem] | str | LRItem, value: int | str
    ) -> None:
        idx = len(self._keepalive)
        self._keepalive.append(key)
        self._contents[id(key)] = key, value, idx

    def __delitem__(self, key: list[Any]) -> None:
        del self._contents[id(key)]
        for idx, obj in enumerate(self._keepalive):
            if obj is key:
                del self._keepalive[idx]
                break

    def __len__(self) -> int:
        return len(self._contents)

    def __iter__(self) -> Iterator[list[Any]]:
        for key, _, _ in itervalues(self._contents):
            yield key


class Counter:
    def __init__(self) -> None:
        self.value = 0

    def incr(self) -> None:
        self.value += 1


def itervalues(d):
    return d.values()


def iteritems(d):
    return d.items()
