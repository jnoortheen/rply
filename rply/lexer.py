from __future__ import annotations

from typing import TYPE_CHECKING, Any

from rply.errors import LexingError
from rply.token import SourcePosition, Token

if TYPE_CHECKING:
    from rply.lexergenerator import Match, Rule


class Lexer:
    def __init__(self, rules: list[Any | Rule], ignore_rules: list[Any | Rule]) -> None:
        self.rules = rules
        self.ignore_rules = ignore_rules

    def lex(self, s: str) -> LexerStream:
        return LexerStream(self, s)


class LexerStream:
    def __init__(self, lexer: Lexer, s: str) -> None:
        self.lexer = lexer
        self.s = s
        self.idx = 0

        self._lineno = 1
        self._colno = 1

    def __iter__(self) -> LexerStream:
        return self

    def _update_pos(self, match: Match) -> int:
        self.idx = match.end
        self._lineno += self.s.count("\n", match.start, match.end)
        last_nl = self.s.rfind("\n", 0, match.start)
        if last_nl < 0:
            return match.start + 1
        else:
            return match.start - last_nl

    def next(self) -> Token:
        while True:
            if self.idx >= len(self.s):
                raise StopIteration
            for rule in self.lexer.ignore_rules:
                match = rule.matches(self.s, self.idx)
                if match:
                    self._update_pos(match)
                    break
            else:
                break

        for rule in self.lexer.rules:
            match = rule.matches(self.s, self.idx)
            if match:
                lineno = self._lineno
                self._colno = self._update_pos(match)
                source_pos = SourcePosition(match.start, lineno, self._colno)
                token = Token(rule.name, self.s[match.start : match.end], source_pos)
                return token
        else:
            raise LexingError(None, SourcePosition(self.idx, self._lineno, self._colno))

    def __next__(self) -> Token:
        return self.next()
