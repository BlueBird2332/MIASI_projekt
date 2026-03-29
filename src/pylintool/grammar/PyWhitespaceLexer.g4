lexer grammar PyWhitespaceLexer;

// ── Keywords that define block structure ──────────────────────────
DEF       : 'def';
CLASS     : 'class';
IF        : 'if';
ELIF      : 'elif';
ELSE      : 'else';
FOR       : 'for';
WHILE     : 'while';
TRY       : 'try';
EXCEPT    : 'except';
FINALLY   : 'finally';
WITH      : 'with';
RETURN    : 'return';
YIELD     : 'yield';
PASS      : 'pass';
RAISE     : 'raise';
BREAK     : 'break';
CONTINUE  : 'continue';
IMPORT    : 'import';
FROM      : 'from';
AS        : 'as';
ASYNC     : 'async';
AWAIT     : 'await';
MATCH     : 'match';
CASE      : 'case';
LAMBDA    : 'lambda';
AND       : 'and';
OR        : 'or';
NOT       : 'not';
IN        : 'in';
IS        : 'is';
NONE      : 'None';
TRUE      : 'True';
FALSE     : 'False';
GLOBAL    : 'global';
NONLOCAL  : 'nonlocal';
DEL       : 'del';
ASSERT    : 'assert';

// ── Structural tokens ────────────────────────────────────────────
COLON     : ':';
LPAREN    : '(';
RPAREN    : ')';
LBRACK    : '[';
RBRACK    : ']';
LBRACE    : '{';
RBRACE    : '}';
COMMA     : ',';
SEMI      : ';';
AT        : '@';
ARROW     : '->';
ASSIGN    : '=';
DOT       : '.';
STAR      : '*';
DOUBLESTAR: '**';
ELLIPSIS  : '...';

// ── Operators ────────────────────────────────────────────────────
OP        : '+=' | '-=' | '*=' | '/=' | '//=' | '%=' | '**='
          | '&=' | '|=' | '^=' | '>>=' | '<<=' | ':='
          | '==' | '!=' | '<=' | '>=' | '<<' | '>>' | '//'
          | [+\-/%&|^~<>!]
          ;

// ── Strings (multiline-aware to avoid false whitespace hits) ────
STRING
    : STRING_PREFIX? ( SHORT_STRING | LONG_STRING )
    ;

fragment STRING_PREFIX
    : [fFbBuUrR]
    | [fFrR] [bBrRfF]
    | [bB] [rR]
    ;

fragment SHORT_STRING
    : '\'' ( ~[\\\r\n'] | '\\' . )* '\''
    | '"'  ( ~[\\\r\n"] | '\\' . )* '"'
    ;

fragment LONG_STRING
    : '\'\'\'' .*? '\'\'\''
    | '"""'    .*? '"""'
    ;

// ── Numbers ──────────────────────────────────────────────────────
NUMBER
    : [0-9] [0-9_]* ( '.' [0-9_]+ )? ( [eE] [+-]? [0-9_]+ )?
    | '0' [xX] [0-9a-fA-F_]+
    | '0' [oO] [0-7_]+
    | '0' [bB] [01_]+
    | '.' [0-9] [0-9_]* ( [eE] [+-]? [0-9_]+ )?
    ;

// ── Identifiers ─────────────────────────────────────────────────
NAME      : [a-zA-Z_] [a-zA-Z0-9_]* ;

// ── Comments — hidden channel so the parser can optionally see them
COMMENT   : '#' ~[\r\n]* -> channel(HIDDEN) ;

// ── Whitespace tokens — KEPT (not skipped) for linting ──────────
NEWLINE
    : '\r'? '\n'
    | '\r'
    ;

LINE_CONTINUATION
    : '\\' ( '\r'? '\n' | '\r' )
    ;

WS : [ \t]+ ;
