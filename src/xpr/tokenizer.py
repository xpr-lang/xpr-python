from __future__ import annotations
from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Optional
from .errors import XprError


class TokenType(Enum):
    Number = auto()
    String = auto()
    Boolean = auto()
    Null = auto()
    TemplateLiteral = auto()
    TemplateHead = auto()
    TemplateMiddle = auto()
    TemplateTail = auto()
    Identifier = auto()
    Plus = auto()
    Minus = auto()
    Star = auto()
    Slash = auto()
    Percent = auto()
    StarStar = auto()
    EqualEqual = auto()
    BangEqual = auto()
    Less = auto()
    Greater = auto()
    LessEqual = auto()
    GreaterEqual = auto()
    AmpAmp = auto()
    PipePipe = auto()
    Bang = auto()
    QuestionQuestion = auto()
    QuestionDot = auto()
    PipeGreater = auto()
    Arrow = auto()
    Question = auto()
    Colon = auto()
    Comma = auto()
    Dot = auto()
    LeftParen = auto()
    RightParen = auto()
    LeftBracket = auto()
    RightBracket = auto()
    LeftBrace = auto()
    RightBrace = auto()
    EOF = auto()


@dataclass
class Token:
    type: TokenType
    value: str
    position: int


def _process_escape(ch: str) -> str:
    return {
        "n": "\n",
        "t": "\t",
        "r": "\r",
        "0": "\0",
        "\\": "\\",
        "'": "'",
        '"': '"',
    }.get(ch, ch)


def tokenize(source: str) -> List[Token]:
    tokens: List[Token] = []
    pos = 0
    length = len(source)

    def peek(offset: int = 0) -> str:
        idx = pos + offset
        return source[idx] if idx < length else ""

    def advance() -> str:
        nonlocal pos
        ch = source[pos] if pos < length else ""
        pos += 1
        return ch

    def read_string(quote: str, start: int) -> Token:
        value = ""
        while pos < length:
            ch = advance()
            if ch == quote:
                return Token(TokenType.String, value, start)
            if ch == "\n":
                raise XprError(f"Unterminated string at position {start}", start)
            if ch == "\\":
                esc = advance()
                value += _process_escape(esc)
            else:
                value += ch
        raise XprError(f"Unterminated string at position {start}", start)

    def read_template_content():
        """Returns (content, ended, interpolation)"""
        content = ""
        while pos < length:
            ch = peek()
            if ch == "`":
                advance()
                return content, True, False
            if ch == "$" and peek(1) == "{":
                advance()
                advance()
                return content, False, True
            if ch == "\\":
                advance()
                nxt = peek()
                if nxt in ("$", "`", "\\"):
                    content += advance()
                else:
                    content += _process_escape(advance())
            else:
                content += advance()
        raise XprError("Unterminated template literal", pos)

    def tokenize_segment() -> List[Token]:
        """Tokenize inside ${...}, tracking brace depth."""
        seg: List[Token] = []
        depth = 1
        while pos < length and depth > 0:
            ch = peek()
            if ch == "{":
                depth += 1
                advance()
                seg.append(Token(TokenType.LeftBrace, "{", pos - 1))
                continue
            if ch == "}":
                depth -= 1
                if depth == 0:
                    advance()
                    break
                advance()
                seg.append(Token(TokenType.RightBrace, "}", pos - 1))
                continue
            saved = pos
            t = next_token()
            if t is not None:
                seg.append(t)
            elif pos == saved:
                advance()
        return seg

    def read_template(start: int) -> None:
        content, ended, interpolation = read_template_content()
        if ended:
            tokens.append(Token(TokenType.TemplateLiteral, content, start))
            return
        tokens.append(Token(TokenType.TemplateHead, content, start))
        seg = tokenize_segment()
        tokens.extend(seg)
        while True:
            part_content, part_ended, _ = read_template_content()
            if part_ended:
                tokens.append(Token(TokenType.TemplateTail, part_content, pos))
                break
            tokens.append(Token(TokenType.TemplateMiddle, part_content, pos))
            seg = tokenize_segment()
            tokens.extend(seg)

    def next_token() -> Optional[Token]:
        nonlocal pos
        # skip whitespace
        while pos < length and source[pos].isspace():
            pos += 1
        if pos >= length:
            return None

        start = pos
        ch = peek()

        # Numbers
        if ch.isdigit():
            num = ""
            while pos < length and source[pos].isdigit():
                num += advance()
            if peek() == "." and peek(1).isdigit():
                num += advance()
                while pos < length and source[pos].isdigit():
                    num += advance()
            if peek() in ("e", "E"):
                num += advance()
                if peek() in ("+", "-"):
                    num += advance()
                while pos < length and source[pos].isdigit():
                    num += advance()
            return Token(TokenType.Number, num, start)

        # Strings
        if ch in ('"', "'"):
            advance()
            return read_string(ch, start)

        # Template literals
        if ch == "`":
            advance()
            read_template(start)
            return None

        # Identifiers and keywords
        if ch.isalpha() or ch == "_":
            ident = ""
            while pos < length and (source[pos].isalnum() or source[pos] == "_"):
                ident += advance()
            if ident in ("true", "false"):
                return Token(TokenType.Boolean, ident, start)
            if ident == "null":
                return Token(TokenType.Null, ident, start)
            return Token(TokenType.Identifier, ident, start)

        # Multi-char operators (order matters)
        two = source[pos : pos + 2]
        if two == "**":
            pos += 2
            return Token(TokenType.StarStar, "**", start)
        if two == "==":
            pos += 2
            return Token(TokenType.EqualEqual, "==", start)
        if two == "!=":
            pos += 2
            return Token(TokenType.BangEqual, "!=", start)
        if two == "<=":
            pos += 2
            return Token(TokenType.LessEqual, "<=", start)
        if two == ">=":
            pos += 2
            return Token(TokenType.GreaterEqual, ">=", start)
        if two == "&&":
            pos += 2
            return Token(TokenType.AmpAmp, "&&", start)
        if two == "||":
            pos += 2
            return Token(TokenType.PipePipe, "||", start)
        if two == "??":
            pos += 2
            return Token(TokenType.QuestionQuestion, "??", start)
        if two == "?.":
            pos += 2
            return Token(TokenType.QuestionDot, "?.", start)
        if two == "|>":
            pos += 2
            return Token(TokenType.PipeGreater, "|>", start)
        if two == "=>":
            pos += 2
            return Token(TokenType.Arrow, "=>", start)

        # Single-char operators
        advance()
        mapping = {
            "+": TokenType.Plus,
            "-": TokenType.Minus,
            "*": TokenType.Star,
            "/": TokenType.Slash,
            "%": TokenType.Percent,
            "!": TokenType.Bang,
            "<": TokenType.Less,
            ">": TokenType.Greater,
            "?": TokenType.Question,
            ":": TokenType.Colon,
            ",": TokenType.Comma,
            ".": TokenType.Dot,
            "(": TokenType.LeftParen,
            ")": TokenType.RightParen,
            "[": TokenType.LeftBracket,
            "]": TokenType.RightBracket,
            "{": TokenType.LeftBrace,
            "}": TokenType.RightBrace,
        }
        if ch in mapping:
            return Token(mapping[ch], ch, start)

        raise XprError(f"Unexpected character '{ch}' at position {start}", start)

    while pos < length:
        while pos < length and source[pos].isspace():
            pos += 1
        if pos >= length:
            break
        t = next_token()
        if t is not None:
            tokens.append(t)

    tokens.append(Token(TokenType.EOF, "", pos))
    return tokens
