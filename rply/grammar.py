from __future__ import annotations

from typing import Any, Callable

from rply.errors import ParserGeneratorError


def rightmost_terminal(
    symbols: list[str | Any], terminals: dict[str, list[Any] | list[Any | int]]
) -> str | None:
    for sym in reversed(symbols):
        if sym in terminals:
            return sym
    return None


class Grammar:
    def __init__(self, terminals: list[str | Any]) -> None:
        # A list of all the productions
        self.productions = [None]
        # A dictionary mapping the names of non-terminals to a list of all
        # productions of that nonterminal
        self.prod_names = {}
        # A dictionary mapping the names of terminals to a list of the rules
        # where they are used
        self.terminals = {t: [] for t in terminals}
        self.terminals["error"] = []
        # A dictionary mapping names of nonterminals to a list of rule numbers
        # where they are used
        self.nonterminals = {}
        self.first = {}
        self.follow = {}
        self.precedence = {}
        self.start = None

    def add_production(
        self,
        prod_name: str,
        syms: list[str | Any],
        func: Callable,
        precedence: str | None,
    ) -> None:
        if prod_name in self.terminals:
            raise ParserGeneratorError("Illegal rule name %r" % prod_name)

        if precedence is None:
            precname = rightmost_terminal(syms, self.terminals)
            prod_prec = self.precedence.get(precname, ("right", 0))
        else:
            try:
                prod_prec = self.precedence[precedence]
            except KeyError:
                raise ParserGeneratorError("Precedence %r doesn't exist" % precedence)

        pnumber = len(self.productions)
        self.nonterminals.setdefault(prod_name, [])

        for t in syms:
            if t in self.terminals:
                self.terminals[t].append(pnumber)
            else:
                self.nonterminals.setdefault(t, []).append(pnumber)

        p = Production(pnumber, prod_name, syms, prod_prec, func)
        self.productions.append(p)

        self.prod_names.setdefault(prod_name, []).append(p)

    def set_precedence(self, term: str, assoc: str, level: int) -> None:
        if term in self.precedence:
            raise ParserGeneratorError("Precedence already specified for %s" % term)
        if assoc not in ["left", "right", "nonassoc"]:
            raise ParserGeneratorError(
                "Precedence must be one of left, right, nonassoc; not %s" % (assoc)
            )
        self.precedence[term] = (assoc, level)

    def set_start(self) -> None:
        start = self.productions[1].name
        self.productions[0] = Production(0, "S'", [start], ("right", 0), None)
        self.nonterminals[start].append(0)
        self.start = start

    def unused_terminals(self) -> list[str | Any]:
        return [t for t, prods in self.terminals.items() if not prods and t != "error"]

    def unused_productions(self) -> list[str | Any]:
        return [p for p, prods in self.nonterminals.items() if not prods]

    def build_lritems(self) -> None:
        """
        Walks the list of productions and builds a complete set of the LR
        items.
        """
        for p in self.productions:
            lastlri = p
            i = 0
            lr_items = []
            while True:
                if i > p.getlength():
                    lri = None
                else:
                    try:
                        before = p.prod[i - 1]
                    except IndexError:
                        before = None
                    try:
                        after = self.prod_names[p.prod[i]]
                    except (IndexError, KeyError):
                        after = []
                    lri = LRItem(p, i, before, after)
                lastlri.lr_next = lri
                if lri is None:
                    break
                lr_items.append(lri)
                lastlri = lri
                i += 1
            p.lr_items = lr_items

    def _first(self, beta: list[str | Any]) -> list[str | Any]:
        result = []
        for x in beta:
            x_produces_empty = False
            for f in self.first[x]:
                if f == "<empty>":
                    x_produces_empty = True
                else:
                    if f not in result:
                        result.append(f)
            if not x_produces_empty:
                break
        else:
            result.append("<empty>")
        return result

    def compute_first(self) -> None:
        for t in self.terminals:
            self.first[t] = [t]

        self.first["$end"] = ["$end"]

        for n in self.nonterminals:
            self.first[n] = []

        changed = True
        while changed:
            changed = False
            for n in self.nonterminals:
                for p in self.prod_names[n]:
                    for f in self._first(p.prod):
                        if f not in self.first[n]:
                            self.first[n].append(f)
                            changed = True

    def compute_follow(self) -> None:
        for k in self.nonterminals:
            self.follow[k] = []

        start = self.start
        self.follow[start] = ["$end"]

        added = True
        while added:
            added = False
            for p in self.productions[1:]:
                for i, B in enumerate(p.prod):
                    if B in self.nonterminals:
                        fst = self._first(p.prod[i + 1 :])
                        has_empty = False
                        for f in fst:
                            if f != "<empty>" and f not in self.follow[B]:
                                self.follow[B].append(f)
                                added = True
                            if f == "<empty>":
                                has_empty = True
                        if has_empty or i == (len(p.prod) - 1):
                            for f in self.follow[p.name]:
                                if f not in self.follow[B]:
                                    self.follow[B].append(f)
                                    added = True


class Production:
    def __init__(
        self,
        num: int,
        name: str,
        prod: list[str | Any],
        precedence: tuple[str, int],
        func: Callable | None,
    ) -> None:
        self.name = name
        self.prod = prod
        self.number = num
        self.func = func
        self.prec = precedence

        self.unique_syms = []
        for s in self.prod:
            if s not in self.unique_syms:
                self.unique_syms.append(s)

        self.lr_items = []
        self.lr_next = None
        self.lr0_added = 0
        self.reduced = 0

    def __repr__(self) -> str:
        return "Production({} -> {})".format(self.name, " ".join(self.prod))

    def getlength(self) -> int:
        return len(self.prod)


class LRItem:
    def __init__(
        self, p: Production, n: int, before: str | None, after: list[Any | Production]
    ) -> None:
        self.name = p.name
        self.prod = p.prod[:]
        self.prod.insert(n, ".")
        self.number = p.number
        self.lr_index = n
        self.lookaheads = {}
        self.unique_syms = p.unique_syms
        self.lr_before = before
        self.lr_after = after

    def __repr__(self):
        return "LRItem({} -> {})".format(self.name, " ".join(self.prod))

    def getlength(self) -> int:
        return len(self.prod)
