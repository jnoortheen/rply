from __future__ import annotations

import re

from rply.lexer import Lexer


class Rule:
    _attrs_ = ["name", "flags", "_pattern"]

    def __init__(self, name: str, pattern: str, flags: int | re.RegexFlag = 0) -> None:
        self.name = name
        self.re = re.compile(pattern, flags=flags)

    def _freeze_(self):
        return True

    def matches(self, s: str, pos: int) -> Match | None:
        m = self.re.match(s, pos)
        return Match(*m.span(0)) if m is not None else None


class Match:
    _attrs_ = ["start", "end"]

    def __init__(self, start: int, end: int) -> None:
        self.start = start
        self.end = end


class LexerGenerator:
    r"""
    A LexerGenerator represents a set of rules that match pieces of text that
    should either be turned into tokens or ignored by the lexer.

    Rules are added using the :meth:`add` and :meth:`ignore` methods:

    >>> from rply import LexerGenerator
    >>> lg = LexerGenerator()
    >>> lg.add('NUMBER', r'\d+')
    >>> lg.add('ADD', r'\+')
    >>> lg.ignore(r'\s+')

    The rules are passed to :func:`re.compile`. If you need additional flags,
    e.g. :const:`re.DOTALL`, you can pass them to :meth:`add` and
    :meth:`ignore` as an additional optional parameter:

    >>> import re
    >>> lg.add('ALL', r'.*', flags=re.DOTALL)

    You can then build a lexer with which you can lex a string to produce an
    iterator yielding tokens:

    >>> lexer = lg.build()
    >>> iterator = lexer.lex('1 + 1')
    >>> iterator.next()
    Token('NUMBER', '1')
    >>> iterator.next()
    Token('ADD', '+')
    >>> iterator.next()
    Token('NUMBER', '1')
    >>> iterator.next()
    Traceback (most recent call last):
    ...
    StopIteration
    """

    def __init__(self) -> None:
        self.rules = []
        self.ignore_rules = []

    def add(self, name: str, pattern: str, flags: int | re.RegexFlag = 0) -> None:
        """
        Adds a rule with the given `name` and `pattern`. In case of ambiguity,
        the first rule added wins.
        """
        self.rules.append(Rule(name, pattern, flags=flags))

    def ignore(self, pattern: str, flags: int | re.RegexFlag = 0) -> None:
        """
        Adds a rule whose matched value will be ignored. Ignored rules will be
        matched before regular ones.
        """
        self.ignore_rules.append(Rule("", pattern, flags=flags))

    def build(self) -> Lexer:
        """
        Returns a lexer instance, which provides a `lex` method that must be
        called with a string and returns an iterator yielding
        :class:`~rply.Token` instances.
        """
        return Lexer(self.rules, self.ignore_rules)
