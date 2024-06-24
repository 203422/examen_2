from flask import Flask, request, render_template
import ply.lex as lex
import ply.yacc as yacc

app = Flask(__name__)

reserved = {
    'int': 'INT',
    'DO': 'DO',
    'ENDDO': 'ENDDO',
    'WHILE': 'WHILE',
    'ENDWHILE': 'ENDWHILE'
}

tokens = [
    'IDENTIFIER',
    'LPAREN',
    'RPAREN',
    'SEMICOLON',
    'PLUS',
    'MINUS',
    'TIMES',
    'DIVIDE',
    'NUMBER',
    'DOT',
    'ASSIGN',
    'EQUAL'
] + list(reserved.values())

t_LPAREN = r'\('
t_RPAREN = r'\)'
t_SEMICOLON = r';'
t_DOT = r'\.'
t_ASSIGN = r'='
t_EQUAL = r'=='
t_PLUS = r'\+'
t_MINUS = r'-'
t_TIMES = r'\*'
t_DIVIDE = r'/'

def t_NUMBER(t):
    r'\d+'
    t.value = int(t.value)
    return t

def t_IDENTIFIER(t):
    r'[a-zA-Z_][a-zA-Z_0-9]*'
    t.type = reserved.get(t.value, 'IDENTIFIER')
    return t

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

t_ignore = ' \t'

def t_error(t):
    print(f"Illegal character '{t.value[0]}' at line {t.lineno}, position {t.lexpos}") 
    t.lexer.skip(1)

lexer = lex.lex()

symbol_table = {}

def p_program(p):
    '''
    program : declarations DO statements ENDDO while_statement ENDWHILE
    '''
    p[0] = ('program', p[1], p[2], p[3], p[4], p[5], p[6])

def p_declarations(p):
    '''
    declarations : declarations declaration
                 | declaration
    '''
    if len(p) == 3:
        p[0] = p[1] + [p[2]]
    else:
        p[0] = [p[1]]

def p_declaration(p):
    '''
    declaration : INT IDENTIFIER ASSIGN NUMBER SEMICOLON
    '''
    identifier = p[2]
    value = p[4]
    symbol_table[identifier] = value
    p[0] = ('declare', identifier, value)

def p_statements(p):
    '''
    statements : statements statement
               | statement
    '''
    if len(p) == 3:
        p[0] = p[1] + [p[2]]
    else:
        p[0] = [p[1]]

def p_statement(p):
    
    '''
    statement : IDENTIFIER ASSIGN expression SEMICOLON
    '''
    identifier = p[1]
    global error_message
    if identifier not in symbol_table:
        error_message = (f"Variable '{identifier}' no declarada")
    expression_value = p[3]
    symbol_table[identifier] = expression_value
    p[0] = ('assign', identifier, expression_value)

def p_expression(p):
    '''
    expression : expression PLUS term
               | expression MINUS term
               | term
    '''
    if len(p) == 4:
        p[0] = ('binop', p[2], p[1], p[3])
    else:
        p[0] = p[1]

def p_term(p):
    '''
    term : term TIMES factor
         | term DIVIDE factor
         | factor
    '''
    if len(p) == 4:
        p[0] = ('binop', p[2], p[1], p[3])
    else:
        p[0] = p[1]

def p_factor(p):
    '''
    factor : NUMBER
           | IDENTIFIER
    '''
    global error_message
    if isinstance(p[1], int):
        p[0] = ('factor', p[1])
    else:
        identifier = p[1]
        if identifier not in symbol_table:
            error_message = (f"Variable '{identifier}' no declarada")
        p[0] = ('factor', identifier)

def p_while_statement(p):
    '''
    while_statement : WHILE LPAREN condition RPAREN
    '''
    p[0] = ('while', p[3])

def p_condition(p):
    '''
    condition : INT IDENTIFIER EQUAL NUMBER
    '''
    identifier = p[2]
    if identifier not in symbol_table:
        raise SyntaxError(f"Variable '{identifier}' no declarada")
    p[0] = ('condition', p[1], identifier, p[3], p[4])

# Manejo de errores
def p_error(p):
    global error_message
    if p:
        error_message = f"Error de sintaxis en '{p.value}', position {p.lexpos}"
    else:
        error_message = "Syntax error at EOF"

error_message = None

def analyze_code(code):
    global error_message
    global symbol_table
    symbol_table = {}  
    error_message = None 
    lexer = lex.lex()
    parser = yacc.yacc()
    lexer.input(code)
    tokens = []
    token_count = {'PR': 0, 'IDENTIFIER': 0, 'NUMBER': 0, 'SYM': 0}

    try:
        while True:
            tok = lexer.token()
            if not tok:
                break
            token_type = tok.type
            if token_type in reserved.values():
                token_count['PR'] += 1
            elif token_type == 'IDENTIFIER':
                token_count['IDENTIFIER'] += 1
            elif token_type == 'NUMBER':
                token_count['NUMBER'] += 1
            else:
                token_count['SYM'] += 1
            tokens.append((tok.type, tok.value, tok.lineno, tok.lexpos))
        result = parser.parse(code)
    except SyntaxError as e:
        error_message = str(e)
        result = None

    return tokens, token_count, result

@app.route('/', methods=['GET', 'POST'])
def index():
    tokens = []
    result = None
    token_count = {}
    syntax_error = None 
    if request.method == 'POST':
        code = request.form['code']
        tokens, token_count, result = analyze_code(code)
        syntax_error = error_message
        print(symbol_table)
        print(result)
    return render_template('index.html', tokens=tokens, token_count=token_count, result=result, syntax_error=syntax_error)

if __name__ == '__main__':
    app.run(debug=True)
