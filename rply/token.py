from __future__ import annotations


class BaseBox:
    """
    A base class for polymorphic boxes that wrap parser results. Simply use
    this as a base class for anything you return in a production function of a
    parser. This is necessary because RPython unlike Python expects functions
    to always return objects of the same type.
    """

    _attrs_ = []


class Token(BaseBox):
    """
    Represents a syntactically relevant piece of text.

    :param name: A string describing the kind of text represented.
    :param value: The actual text represented.
    :param source_pos: A :class:`SourcePosition` object representing the
                       position of the first character in the source from which
                       this token was generated.
    """

    def __init__(
        self, name: str, value: str, source_pos: SourcePosition | None = None
    ) -> None:
        self.name = name
        self.value = value
        self.source_pos = source_pos

    def __repr__(self) -> str:
        return f"Token({self.name!r}, {self.value!r})"

    def __eq__(self, other: int | Token) -> bool:
        if not isinstance(other, Token):
            return NotImplemented
        return self.name == other.name and self.value == other.value

    def gettokentype(self) -> str:
        """
        Returns the type or name of the token.
        """
        return self.name

    def getsourcepos(self) -> SourcePosition:
        """
        Returns a :class:`SourcePosition` instance, describing the position of
        this token's first character in the source.
        """
        return self.source_pos

    def getstr(self) -> str:
        """
        Returns the string represented by this token.
        """
        return self.value


class SourcePosition:
    """
    Represents the position of a character in some source string.

    :param idx: The index of the character in the source.
    :param lineno: The number of the line in which the character occurs.
    :param colno: The number of the column in which the character occurs.

    The values passed to this object can be retrieved using the identically
    named attributes.
    """

    def __init__(self, idx: int, lineno: int, colno: int) -> None:
        self.idx = idx
        self.lineno = lineno
        self.colno = colno

    def __repr__(self) -> str:
        return "SourcePosition(idx={}, lineno={}, colno={})".format(
            self.idx, self.lineno, self.colno
        )
