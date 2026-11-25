"""RQL Lexer: converts an RQL string into a sequence of Tokens (SRP)."""

from __future__ import annotations

from rql.lexer.tokens import Token, TokenType

_KEYWORDS: dict[str, TokenType] = {
    "AND": TokenType.AND,
    "OR": TokenType.OR,
    "NOT": TokenType.NOT,
    "IN": TokenType.IN,
    "IS": TokenType.IS,
    "WAS": TokenType.WAS,
    "CHANGED": TokenType.CHANGED,
    "ORDER": TokenType.ORDER_BY,
    "BY": TokenType.BY,
    "ASC": TokenType.ASC,
    "DESC": TokenType.DESC,
}


class RqlLexer:
    """Tokenizes an RQL query string into a list of Tokens."""

    def __init__(self, input_text: str) -> None:
        self._input = input_text
        self._pos = 0
        self._length = len(input_text)

    def tokenize(self) -> list[Token]:
        """Scans the input string and returns all tokens terminated by TokenType.EOF."""
        tokens: list[Token] = []
        while self._pos < self._length:
            self._skip_whitespace()
            if self._pos >= self._length:
                break

            ch = self._input[self._pos]

            if ch in ('"', "'"):
                tokens.append(self._read_string(ch))
                continue

            if ch.isdigit() or (
                ch == "-"
                and self._pos + 1 < self._length
                and self._input[self._pos + 1].isdigit()
            ):
                tokens.append(self._read_number())
                continue

            if ch == "(":
                tokens.append(Token(TokenType.LPAREN, "(", self._pos))
                self._pos += 1
                continue
            if ch == ")":
                tokens.append(Token(TokenType.RPAREN, ")", self._pos))
                self._pos += 1
                continue
            if ch == ",":
                tokens.append(Token(TokenType.COMMA, ",", self._pos))
                self._pos += 1
                continue
            if ch == "!" and self._peek(1) == "=":
                tokens.append(Token(TokenType.NOT_EQUALS, "!=", self._pos))
                self._pos += 2
                continue
            if ch == "=":
                tokens.append(Token(TokenType.EQUALS, "=", self._pos))
                self._pos += 1
                continue
            if ch == "<" and self._peek(1) == "=":
                tokens.append(Token(TokenType.LESS_THAN_OR_EQUAL, "<=", self._pos))
                self._pos += 2
                continue
            if ch == "<":
                tokens.append(Token(TokenType.LESS_THAN, "<", self._pos))
                self._pos += 1
                continue
            if ch == ">" and self._peek(1) == "=":
                tokens.append(Token(TokenType.GREATER_THAN_OR_EQUAL, ">=", self._pos))
                self._pos += 2
                continue
            if ch == ">":
                tokens.append(Token(TokenType.GREATER_THAN, ">", self._pos))
                self._pos += 1
                continue
            if ch == "~":
                tokens.append(Token(TokenType.CONTAINS, "~", self._pos))
                self._pos += 1
                continue
            if ch == "!" and self._peek(1) == "~":
                tokens.append(Token(TokenType.NOT_CONTAINS, "!~", self._pos))
                self._pos += 2
                continue
            if ch.isalpha() or ch == "_":
                tokens.append(self._read_identifier_or_keyword())
                continue

            # Skip unknown character (matches C# RqlLexer behavior)
            self._pos += 1

        tokens.append(Token(TokenType.EOF, "", self._pos))
        return tokens

    def _peek(self, offset: int = 0) -> str:
        idx = self._pos + offset
        return self._input[idx] if idx < self._length else "\0"

    def _skip_whitespace(self) -> None:
        while self._pos < self._length and self._input[self._pos].isspace():
            self._pos += 1

    def _read_string(self, quote: str) -> Token:
        start = self._pos
        self._pos += 1
        chars: list[str] = []
        while self._pos < self._length and self._input[self._pos] != quote:
            if self._input[self._pos] == "\\" and self._pos + 1 < self._length:
                self._pos += 1
                chars.append(self._input[self._pos])
                self._pos += 1
            else:
                chars.append(self._input[self._pos])
                self._pos += 1
        if self._pos < self._length:
            self._pos += 1  # closing quote
        return Token(TokenType.STRING, "".join(chars), start)

    def _read_number(self) -> Token:
        start = self._pos
        chars: list[str] = []
        if self._input[self._pos] == "-":
            chars.append("-")
            self._pos += 1
        while self._pos < self._length and (
            self._input[self._pos].isdigit() or self._input[self._pos] == "."
        ):
            chars.append(self._input[self._pos])
            self._pos += 1
        return Token(TokenType.NUMBER, "".join(chars), start)

    def _read_identifier_or_keyword(self) -> Token:
        start = self._pos
        chars: list[str] = []
        while self._pos < self._length and (
            self._input[self._pos].isalnum() or self._input[self._pos] in ("_", "-")
        ):
            chars.append(self._input[self._pos])
            self._pos += 1

        word = "".join(chars)
        token_type = _KEYWORDS.get(word.upper(), TokenType.IDENTIFIER)

        # Compound keyword lookahead with rollback
        if token_type == TokenType.NOT:
            saved = self._pos
            self._skip_whitespace()
            if self._peek_word("IN"):
                self._skip_word("IN")
                return Token(TokenType.NOT_IN, "NOT IN", start)
            if self._peek_word("WAS"):
                self._skip_word("WAS")
                self._skip_whitespace()
                if self._peek_word("IN"):
                    self._skip_word("IN")
                    return Token(TokenType.WAS_NOT_IN, "WAS NOT IN", start)
                return Token(TokenType.WAS_NOT, "WAS NOT", start)
            self._pos = saved

        elif token_type == TokenType.IS:
            saved = self._pos
            self._skip_whitespace()
            if self._peek_word("NOT"):
                self._skip_word("NOT")
                return Token(TokenType.IS_NOT, "IS NOT", start)
            self._pos = saved

        elif token_type == TokenType.WAS:
            saved = self._pos
            self._skip_whitespace()
            if self._peek_word("IN"):
                self._skip_word("IN")
                return Token(TokenType.WAS_IN, "WAS IN", start)
            if self._peek_word("NOT"):
                self._skip_word("NOT")
                self._skip_whitespace()
                if self._peek_word("IN"):
                    self._skip_word("IN")
                    return Token(TokenType.WAS_NOT_IN, "WAS NOT IN", start)
                return Token(TokenType.WAS_NOT, "WAS NOT", start)
            self._pos = saved

        return Token(token_type, word, start)

    def _peek_word(self, word: str) -> bool:
        end = self._pos + len(word)
        if end > self._length:
            return False
        if self._input[self._pos : end].upper() != word.upper():
            return False
        return end >= self._length or not (
            self._input[end].isalnum() or self._input[end] in ("_", "-")
        )

    def _skip_word(self, word: str) -> None:
        self._pos += len(word)
