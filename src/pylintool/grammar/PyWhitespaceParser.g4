parser grammar PyWhitespaceParser;

options { tokenVocab = PyWhitespaceLexer; }

// ── Entry point ──────────────────────────────────────────────────
file_input
    : file_line* EOF
    ;

file_line
    : NEWLINE                                                # blankLine
    | leading_ws? line_content trailing_ws? NEWLINE           # contentLine
    | leading_ws? line_content trailing_ws? EOF               # lastLine
    ;

leading_ws  : WS ;
trailing_ws : WS ;

// ── Line content (sequence of tokens + inline whitespace) ────────
line_content
    : token_or_ws+
    ;

token_or_ws
    : any_token
    | inline_ws
    | continuation
    ;

inline_ws
    : WS
    ;

continuation
    : LINE_CONTINUATION WS?
    ;

// ── Tokens (everything the linter might inspect) ─────────────────
any_token
    : keyword
    | structural
    | literal
    | NAME
    | OP
    | COMMENT
    ;

keyword
    : DEF | CLASS | IF | ELIF | ELSE | FOR | WHILE
    | TRY | EXCEPT | FINALLY | WITH | RETURN | YIELD | PASS
    | RAISE | BREAK | CONTINUE
    | IMPORT | FROM | AS | ASYNC | AWAIT | MATCH | CASE
    | LAMBDA | AND | OR | NOT | IN | IS
    | NONE | TRUE | FALSE | GLOBAL | NONLOCAL | DEL | ASSERT
    ;

structural
    : COLON | LPAREN | RPAREN | LBRACK | RBRACK | LBRACE | RBRACE
    | COMMA | SEMI | AT | ARROW | ASSIGN | DOT
    | STAR | DOUBLESTAR | ELLIPSIS
    ;

literal
    : STRING
    | NUMBER
    ;
