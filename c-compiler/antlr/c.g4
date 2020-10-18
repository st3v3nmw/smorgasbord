grammar c;

statements
    : statement statements;

statement
    : 'print ' expression ';';

expression
    : additive_expression;

additive_expression
    : multiplicative_expression
    | additive_expression additive_op multiplicative_expression;

multiplicative_expression
    : NUMBER
    | NUMBER multiplicative_op multiplicative_expression;

additive_op
    : '+'
    | '-'; // additive inverse

multiplicative_op
    : '*'
    | '/'; // multiplicative inverse

NUMBER
    : [0-9]+;

WHITESPACE
    : ' ' -> skip;