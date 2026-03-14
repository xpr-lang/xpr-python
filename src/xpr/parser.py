from __future__ import annotations
from typing import Any, List, Optional
from .errors import XprError
from .tokenizer import Token, TokenType
from .types import (
    Expression,
    NumberLiteral,
    StringLiteral,
    BooleanLiteral,
    NullLiteral,
    ArrayExpression,
    ObjectExpression,
    Property,
    SpreadProperty,
    Identifier,
    MemberExpression,
    BinaryExpression,
    LogicalExpression,
    UnaryExpression,
    ConditionalExpression,
    ArrowFunction,
    CallExpression,
    TemplateLiteral,
    PipeExpression,
    SpreadElement,
    LetExpression,
)

BP_PIPE = 10
BP_TERNARY = 20
BP_NULLISH = 30
BP_OR = 40
BP_AND = 50
BP_EQUALITY = 60
BP_COMPARE = 70
BP_ADD = 80
BP_MUL = 90
BP_EXP = 100
BP_UNARY = 110
BP_POSTFIX = 120


def _left_bp(token: Token) -> int:
    t = token.type
    if t == TokenType.PipeGreater:
        return BP_PIPE
    if t == TokenType.Question:
        return BP_TERNARY
    if t == TokenType.QuestionQuestion:
        return BP_NULLISH
    if t == TokenType.PipePipe:
        return BP_OR
    if t == TokenType.AmpAmp:
        return BP_AND
    if t in (TokenType.EqualEqual, TokenType.BangEqual):
        return BP_EQUALITY
    if t in (
        TokenType.Less,
        TokenType.Greater,
        TokenType.LessEqual,
        TokenType.GreaterEqual,
    ):
        return BP_COMPARE
    if t in (TokenType.Plus, TokenType.Minus):
        return BP_ADD
    if t in (TokenType.Star, TokenType.Slash, TokenType.Percent):
        return BP_MUL
    if t == TokenType.StarStar:
        return BP_EXP
    if t in (
        TokenType.Dot,
        TokenType.QuestionDot,
        TokenType.LeftBracket,
        TokenType.LeftParen,
    ):
        return BP_POSTFIX
    return 0


class Parser:
    def __init__(self, tokens: List[Token]):
        self._tokens = tokens
        self._pos = 0

    def _peek(self) -> Token:
        if self._pos < len(self._tokens):
            return self._tokens[self._pos]
        return Token(TokenType.EOF, "", -1)

    def _advance(self) -> Token:
        t = (
            self._tokens[self._pos]
            if self._pos < len(self._tokens)
            else Token(TokenType.EOF, "", -1)
        )
        if t.type != TokenType.EOF:
            self._pos += 1
        return t

    def _expect(self, ttype: TokenType) -> Token:
        t = self._peek()
        if t.type != ttype:
            raise XprError(
                f"Expected {ttype} but got {t.type} at position {t.position}",
                t.position,
            )
        return self._advance()

    def _parse_arg_list(self) -> List[Expression]:
        args: List[Expression] = []
        while self._peek().type not in (TokenType.RightParen, TokenType.EOF):
            if self._peek().type == TokenType.DotDotDot:
                pos = self._peek().position
                self._advance()
                args.append(SpreadElement(argument=self.expression(0), position=pos))
            else:
                args.append(self.expression(0))
            if self._peek().type == TokenType.Comma:
                self._advance()
            else:
                break
        return args

    def _nud(self, token: Token) -> Expression:
        pos = token.position
        t = token.type

        if t == TokenType.Number:
            return NumberLiteral(value=float(token.value), position=pos)

        if t == TokenType.String:
            return StringLiteral(value=token.value, position=pos)

        if t == TokenType.Boolean:
            return BooleanLiteral(value=(token.value == "true"), position=pos)

        if t == TokenType.Null:
            return NullLiteral(position=pos)

        if t == TokenType.TemplateLiteral:
            return TemplateLiteral(quasis=[token.value], expressions=[], position=pos)

        if t == TokenType.TemplateHead:
            quasis: List[str] = [token.value]
            expressions: List[Expression] = []
            while True:
                expressions.append(self.expression(0))
                nxt = self._peek()
                if nxt.type == TokenType.TemplateTail:
                    quasis.append(self._advance().value)
                    break
                elif nxt.type == TokenType.TemplateMiddle:
                    quasis.append(self._advance().value)
                else:
                    raise XprError(
                        f"Unexpected token in template literal at position {nxt.position}",
                        nxt.position,
                    )
            return TemplateLiteral(quasis=quasis, expressions=expressions, position=pos)

        if t == TokenType.Identifier:
            ident = Identifier(name=token.value, position=pos)
            if self._peek().type == TokenType.Arrow:
                self._advance()
                body = self.expression(0)
                return ArrowFunction(params=[token.value], body=body, position=pos)
            return ident

        if t == TokenType.LeftParen:
            if self._peek().type == TokenType.RightParen:
                self._advance()
                self._expect(TokenType.Arrow)
                body = self.expression(0)
                return ArrowFunction(params=[], body=body, position=pos)
            first = self.expression(0)
            if self._peek().type == TokenType.Comma:
                params: List[str] = []
                if not isinstance(first, Identifier):
                    raise XprError(
                        f"Arrow function params must be identifiers at position {pos}",
                        pos,
                    )
                params.append(first.name)
                while self._peek().type == TokenType.Comma:
                    self._advance()
                    p = self._expect(TokenType.Identifier)
                    params.append(p.value)
                self._expect(TokenType.RightParen)
                self._expect(TokenType.Arrow)
                body = self.expression(0)
                return ArrowFunction(params=params, body=body, position=pos)
            self._expect(TokenType.RightParen)
            if isinstance(first, Identifier) and self._peek().type == TokenType.Arrow:
                self._advance()
                body = self.expression(0)
                return ArrowFunction(params=[first.name], body=body, position=pos)
            return first

        if t == TokenType.Let:
            name_tok = self._expect(TokenType.Identifier)
            self._expect(TokenType.Equal)
            value = self.expression(0)
            self._expect(TokenType.Semicolon)
            if self._peek().type == TokenType.EOF:
                raise XprError("Expected expression after ';'", self._peek().position)
            body = self.expression(0)
            return LetExpression(
                name=name_tok.value, value=value, body=body, position=pos
            )

        if t == TokenType.LeftBracket:
            elements: List[Expression] = []
            while self._peek().type not in (TokenType.RightBracket, TokenType.EOF):
                if self._peek().type == TokenType.DotDotDot:
                    spread_pos = self._peek().position
                    self._advance()
                    arg = self.expression(0)
                    elements.append(SpreadElement(argument=arg, position=spread_pos))
                else:
                    elements.append(self.expression(0))
                if self._peek().type == TokenType.Comma:
                    self._advance()
                else:
                    break
            self._expect(TokenType.RightBracket)
            return ArrayExpression(elements=elements, position=pos)

        if t == TokenType.LeftBrace:
            properties: List[Any] = []
            while self._peek().type not in (TokenType.RightBrace, TokenType.EOF):
                if self._peek().type == TokenType.DotDotDot:
                    spread_pos = self._peek().position
                    self._advance()
                    arg = self.expression(0)
                    properties.append(SpreadProperty(argument=arg, position=spread_pos))
                else:
                    key_tok = self._peek()
                    if key_tok.type == TokenType.Identifier:
                        key = self._advance().value
                    elif key_tok.type == TokenType.String:
                        key = self._advance().value
                    else:
                        raise XprError(
                            f"Expected object key at position {key_tok.position}",
                            key_tok.position,
                        )
                    self._expect(TokenType.Colon)
                    value = self.expression(0)
                    properties.append(
                        Property(key=key, value=value, position=key_tok.position)
                    )
                if self._peek().type == TokenType.Comma:
                    self._advance()
                else:
                    break
            self._expect(TokenType.RightBrace)
            return ObjectExpression(properties=properties, position=pos)

        if t == TokenType.Bang:
            arg = self.expression(BP_UNARY)
            return UnaryExpression(op="!", argument=arg, position=pos)

        if t == TokenType.Minus:
            arg = self.expression(BP_UNARY)
            return UnaryExpression(op="-", argument=arg, position=pos)

        raise XprError(
            f"Unexpected token {token.type} ('{token.value}') at position {pos}", pos
        )

    def _led(self, left: Expression, token: Token) -> Expression:
        pos = token.position
        t = token.type

        if t in (TokenType.Plus, TokenType.Minus):
            right = self.expression(BP_ADD)
            return BinaryExpression(
                op=token.value, left=left, right=right, position=pos
            )

        if t in (TokenType.Star, TokenType.Slash, TokenType.Percent):
            right = self.expression(BP_MUL)
            return BinaryExpression(
                op=token.value, left=left, right=right, position=pos
            )

        if t == TokenType.StarStar:
            right = self.expression(BP_EXP - 1)
            return BinaryExpression(op="**", left=left, right=right, position=pos)

        if t in (TokenType.EqualEqual, TokenType.BangEqual):
            right = self.expression(BP_EQUALITY)
            return BinaryExpression(
                op=token.value, left=left, right=right, position=pos
            )

        if t in (
            TokenType.Less,
            TokenType.Greater,
            TokenType.LessEqual,
            TokenType.GreaterEqual,
        ):
            right = self.expression(BP_COMPARE)
            return BinaryExpression(
                op=token.value, left=left, right=right, position=pos
            )

        if t == TokenType.AmpAmp:
            right = self.expression(BP_AND)
            return LogicalExpression(op="&&", left=left, right=right, position=pos)

        if t == TokenType.PipePipe:
            right = self.expression(BP_OR)
            return LogicalExpression(op="||", left=left, right=right, position=pos)

        if t == TokenType.QuestionQuestion:
            right = self.expression(BP_NULLISH)
            return LogicalExpression(op="??", left=left, right=right, position=pos)

        if t == TokenType.Dot:
            prop = self._expect(TokenType.Identifier)
            return MemberExpression(
                object=left,
                property=prop.value,
                computed=False,
                optional=False,
                position=pos,
            )

        if t == TokenType.QuestionDot:
            if self._peek().type == TokenType.LeftParen:
                self._advance()
                args = self._parse_arg_list()
                self._expect(TokenType.RightParen)
                return CallExpression(
                    callee=left, arguments=args, optional=True, position=pos
                )
            prop = self._expect(TokenType.Identifier)
            return MemberExpression(
                object=left,
                property=prop.value,
                computed=False,
                optional=True,
                position=pos,
            )

        if t == TokenType.LeftBracket:
            index = self.expression(0)
            self._expect(TokenType.RightBracket)
            return MemberExpression(
                object=left, property=index, computed=True, optional=False, position=pos
            )

        if t == TokenType.LeftParen:
            args = self._parse_arg_list()
            self._expect(TokenType.RightParen)
            return CallExpression(
                callee=left, arguments=args, optional=False, position=pos
            )

        if t == TokenType.PipeGreater:
            right = self.expression(BP_PIPE)
            return PipeExpression(left=left, right=right, position=pos)

        if t == TokenType.Question:
            consequent = self.expression(0)
            self._expect(TokenType.Colon)
            alternate = self.expression(BP_TERNARY - 1)
            return ConditionalExpression(
                test=left, consequent=consequent, alternate=alternate, position=pos
            )

        raise XprError(f"Unexpected infix token {token.type} at position {pos}", pos)

    def expression(self, rbp: int) -> Expression:
        token = self._advance()
        if token.type == TokenType.EOF:
            raise XprError("Unexpected end of expression", token.position)
        left = self._nud(token)
        while rbp < _left_bp(self._peek()):
            op = self._advance()
            left = self._led(left, op)
        return left

    def parse(self) -> Expression:
        if self._peek().type == TokenType.EOF:
            raise XprError("Empty expression", 0)
        expr = self.expression(0)
        if self._peek().type != TokenType.EOF:
            t = self._peek()
            raise XprError(
                f"Unexpected token {t.type} at position {t.position}", t.position
            )
        return expr


def parse(tokens: List[Token]) -> Expression:
    return Parser(tokens).parse()
