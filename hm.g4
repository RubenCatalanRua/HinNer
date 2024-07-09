grammar hm;
root : (typedec)* expr?;

typedec : (SYM|NUM) '::' typ;

typ : TYP arrow typ  # typeRec
     | TYP           # typeOnly
     ;

expr : LPAR expr RPAR # paren
     | expr expr # appl
     | ABS expr arrow expr # abstr
     | NUM              # numero
     | ID               # elem
     | SYM              # symbol
     ;

ID  : ('a'..'z');   // variables as single lowercase letters
TYP : ('A'..'Z');
NUM : [0-9]+ ;
SYM : '(' ('+' | '-' | '*' | '/') ')';
LPAR : '(' ;
RPAR : ')' ;
arrow : '->' ;
ABS  : '\\' ;
WS  : [ \t\n\r]+ -> skip ;