import sys

from JackTokenizer import *

RETURN_STATEMENT_TAG = "returnStatement"

CLASS_VAR_DEC_TAG = "classVarDec"

ILLEGAL_STATEMENT_ERROR = "illegal statement"

EXPRESSION_LIST_TAG = "expressionList"

TERM_TAG = "term"

EXPRESSION_TAG = "expression"

IF_STATEMENT_TAG = "ifStatement"

LET_STATEMENT_TAG = "letStatement"

VAR_DEC_TAG = "varDec"

SUBROUTINE_BODY_TAG = "subroutineBody"

PARAMETER_LIST_TAG = "parameterList"

SUBROUTINE_DEC_TAG = "subroutineDec"

IS_ENDING_TAG = True

DO_STATEMENT_TAG = "doStatement"

STATEMENTS_TAG = "statements"

CLASS_TAG = "class"

COMPILE_CLASS_ERROR = "invalid input in compile class"

COMPILE_TERM_ERROR = "invalid input in compile term"

CLASS_VAR_KEYWORDS = ['static', 'field']

TYPE_KEYWORDS = ['int', 'char', 'boolean']

SUBROUTINE = ['constructor', 'function', 'method']

UNARY_OPS = ['-', '~']

KEYWORD_CONST = ['true', 'false', 'null', 'this']

STATEMENTS = ['let', 'if', 'while', 'do', 'return']

TOKEN_TYPE_STR = {"KEYWORD": "keyword", "SYMBOL": "symbol",
                  "IDENTIFIER": "identifier", "INT_CONST": "integerConstant",
                  "STRING_CONST": "stringConstant"}
OPERATIONS = ['+', '-', '=', '>', '<', "*", "/", "&", "|"]


class CompilationEngine:
    """
    The compilation engine compile the jack code given in the input file
    into an xml code saved in the out_file
    """

    def __init__(self, in_file, out_file):
        """
        A compilation engine constructor
        :param in_file: the file we are currently compiling
        :param out_file: the file where we save the output
        """
        self.tokenizer = JackTokenizer(in_file)
        self.out_file = open(out_file, 'w')
        self._indent_count = 0

    def compile_class(self):
        """
        compiles a class according to the grammar
        """
        self._write_outer_tag(CLASS_TAG)
        self.tokenizer.advance()
        if self.tokenizer.key_word() != CLASS_TAG:
            print(COMPILE_CLASS_ERROR)
            sys.exit()
        self._write_token(self.tokenizer.token_type())
        self._check_write_name()
        self._check_write_symbol("{")
        # there may be multiple variable declarations
        while self._check_if_var_dec():
            self.compile_class_var_dec()
        # there may be multiple subroutine declarations
        while self._check_subroutine_dec():
            self.compile_subroutine_dec()
        self._check_write_symbol("}")
        self._write_outer_tag(CLASS_TAG, IS_ENDING_TAG)

    def compile_class_var_dec(self):
        """
        compiles the class's variables declarations
        """
        self._write_outer_tag(CLASS_VAR_DEC_TAG)
        # we only come in the function if the current token is correct so we
        # can just write it
        self._write_token(self.tokenizer.token_type())
        self._check_write_type()
        self._check_write_name()
        while self._check_if_comma():  # there are more variables
            self._check_write_symbol(",")
            self._check_write_name()
        self._check_write_symbol(";")
        self._write_outer_tag(CLASS_VAR_DEC_TAG, IS_ENDING_TAG)

    def compile_subroutine_dec(self):
        """
        compiles the class's subroutine (methods and functions) declarations
        """
        self._write_outer_tag(SUBROUTINE_DEC_TAG)
        # we only come in the function if the current token is correct so we
        # can just write it
        self._write_token(self.tokenizer.token_type())
        # the function is either void or has a type
        if self.tokenizer.key_word() == 'void':
            self._write_token(self.tokenizer.token_type())
        else:
            self._check_write_type()
        self._check_write_name()
        self._check_write_symbol("(")
        self.compile_parameter_list()
        self._check_write_symbol(")")
        self.compile_subroutine_body()
        self._write_outer_tag(SUBROUTINE_DEC_TAG, IS_ENDING_TAG)

    def compile_parameter_list(self):
        """
        compiles the parameter list for the subroutines
        """
        self._write_outer_tag(PARAMETER_LIST_TAG)
        # if curr_token is ')' it means the param list is empty
        if self.tokenizer.symbol() != ')':
            self._check_write_type()
            self._check_write_name()
            while self._check_if_comma():  # there are more params
                self._check_write_symbol(",")
                self._check_write_type()
                self._check_write_name()
        self._write_outer_tag(PARAMETER_LIST_TAG, IS_ENDING_TAG)

    def compile_subroutine_body(self):
        """
        compiles the body of the subroutine
        """
        self._write_outer_tag(SUBROUTINE_BODY_TAG)
        self._check_write_symbol("{")
        # there may be multiple variable declarations at the beginning of
        # the subroutine
        while self.tokenizer.key_word() == 'var':
            self.compile_var_dec()
        self.compile_statements()
        self._check_write_symbol("}")
        self._write_outer_tag(SUBROUTINE_BODY_TAG, IS_ENDING_TAG)

    def compile_var_dec(self):
        """
        compiles the variable declarations
        """
        self._write_outer_tag(VAR_DEC_TAG)
        self._write_token(self.tokenizer.token_type())
        self._check_write_type()
        self._check_write_name()
        # there may be multiple variable names in the dec
        while self._check_if_comma():
            self._check_write_symbol(",")
            self._check_write_name()
        self._check_write_symbol(";")
        self._write_outer_tag(VAR_DEC_TAG, IS_ENDING_TAG)

    def compile_statements(self):
        """
        compiles the statements (0 or more statements)
        """
        self._write_outer_tag(STATEMENTS_TAG)
        while self._check_if_statement():
            if self.tokenizer.key_word() == 'let':
                self.compile_let()
            elif self.tokenizer.key_word() == 'if':
                self.compile_if()
            elif self.tokenizer.key_word() == 'while':
                self.compile_while()
            elif self.tokenizer.key_word() == 'do':
                self.compile_do()
            elif self.tokenizer.key_word() == 'return':
                self.compile_return()
        self._write_outer_tag(STATEMENTS_TAG, IS_ENDING_TAG)

    def compile_do(self):
        """
        compiles the do statement
        """
        self._write_outer_tag(DO_STATEMENT_TAG)
        self._write_token(self.tokenizer.token_type())
        self.compile_subroutine_call()
        self._check_write_symbol(";")
        self._write_outer_tag(DO_STATEMENT_TAG, IS_ENDING_TAG)

    def compile_let(self):
        """
        compiles the let statement
        """
        self._write_outer_tag(LET_STATEMENT_TAG)
        self._write_token(self.tokenizer.token_type())
        self._check_write_name()
        if self.tokenizer.symbol() == '[':  # if there is an array
            self._check_write_symbol("[")
            self.compile_expression()
            self._check_write_symbol("]")
        self._check_write_symbol("=")
        self.compile_expression()
        self._check_write_symbol(";")
        self._write_outer_tag(LET_STATEMENT_TAG, IS_ENDING_TAG)

    def compile_if(self):
        """
        compiles the if statements
        """
        self._write_outer_tag(IF_STATEMENT_TAG)
        self._write_token(self.tokenizer.token_type())
        self._check_write_symbol("(")
        self.compile_expression()
        self._check_write_symbol(")")
        self._check_write_symbol("{")
        self.compile_statements()
        self._check_write_symbol("}")
        # there can also be an if else scenario
        if self.tokenizer.key_word() == 'else':
            self._write_token(self.tokenizer.token_type())
            self._check_write_symbol("{")
            self.compile_statements()
            self._check_write_symbol("}")
        self._write_outer_tag(IF_STATEMENT_TAG, IS_ENDING_TAG)

    def compile_while(self):
        """
        compiles the while statements
        """
        self._write_outer_tag("whileStatement")
        self._write_token(self.tokenizer.token_type())
        self._check_write_symbol("(")
        self.compile_expression()
        self._check_write_symbol(")")
        self._check_write_symbol("{")
        self.compile_statements()
        self._check_write_symbol("}")
        self._write_outer_tag("whileStatement", IS_ENDING_TAG)

    def compile_return(self):
        """
        compiles the return statements
        """
        self._write_outer_tag(RETURN_STATEMENT_TAG)
        self._write_token(self.tokenizer.token_type())
        # if cur token is ; we return nothing, otherwise we return something
        if not self.tokenizer.symbol() == ';':
            self.compile_expression()
        self._check_write_symbol(";")
        self._write_outer_tag(RETURN_STATEMENT_TAG, IS_ENDING_TAG)

    def compile_subroutine_call(self):
        """
        compiles the subroutine calls ( when we actually call a subroutine
        as  opposed to declaring it)
        """
        self._check_write_name()
        # there may be a '.' if it is a foo.bar() scenario (or Foo.bar())
        if self.tokenizer.symbol() == ".":
            self._check_write_symbol(".")
            self._check_write_name()
        self._check_write_symbol("(")
        self.compile_expression_list()
        self._check_write_symbol(")")

    def compile_expression(self):
        """
        compiles expressions which are terms and possibly operators and more
        terms
        """
        self._write_outer_tag(EXPRESSION_TAG)
        self.compile_term()
        # there may be a few operators in one expression
        while self.tokenizer.symbol() in OPERATIONS:
            self._write_op()
            self.compile_term()
        self._write_outer_tag(EXPRESSION_TAG, IS_ENDING_TAG)

    def compile_term(self):
        """
        compiles terms according to the grammar
        """
        self._write_outer_tag(TERM_TAG)
        cur_type = self.tokenizer.token_type()
        # either a string/int constant
        if self.tokenizer.token_type() in ["INT_CONST", "STRING_CONST"]:
            self._write_token(cur_type)
        # or a constant keyword (true, false, null, this)
        elif self.tokenizer.key_word() in KEYWORD_CONST:
            self._write_token(cur_type)
        # or an expression within brown brackets
        elif self.tokenizer.symbol() == '(':
            self._write_token(cur_type)
            self.compile_expression()
            self._check_write_symbol(")")
        # or a unary op and then a term
        elif self.tokenizer.symbol() in UNARY_OPS:
            self._write_op()
            self.compile_term()
        # or it is an identifier which could be:
        elif self.tokenizer.identifier():
            self._compile_term_identifier()
        else:
            print(COMPILE_TERM_ERROR)
            sys.exit()
        self._write_outer_tag(TERM_TAG, IS_ENDING_TAG)

    def _compile_term_identifier(self):
        """
         compiles terms in case of identifier token
        """
        # an array
        if self.tokenizer.get_next_token() == '[':
            self._check_write_name()
            self._check_write_symbol("[")
            self.compile_expression()
            self._check_write_symbol("]")
        # or a subroutine call
        elif self.tokenizer.get_next_token() in [".", "("]:
            self.compile_subroutine_call()
        else:
            self._check_write_name()  # or just a variable name

    def compile_expression_list(self):
        """
        compiles the expression lists
        """
        self._write_outer_tag(EXPRESSION_LIST_TAG)
        # if it is ')' then the expression list is empty
        if self.tokenizer.symbol() != ')':
            self.compile_expression()
            while self._check_if_comma():  # while there are more expressions
                self._write_token(self.tokenizer.token_type())
                self.compile_expression()
        self._write_outer_tag(EXPRESSION_LIST_TAG, IS_ENDING_TAG)

    def _check_if_var_dec(self):
        """
        check if we are currently compiling a variable declaration
        :return: true iff the current token is either 'static' or 'field'
        """
        return self.tokenizer.key_word() in CLASS_VAR_KEYWORDS

    def _check_subroutine_dec(self):
        """
        checks if we are currently compiling a subroutine declaration
        :return: true iff the current token is either 'constructor' or
        'function' or 'method'
        """
        return self.tokenizer.key_word() in SUBROUTINE

    def _check_if_comma(self):
        """
        checks if current token is a comma
        :return: true iff the current token is a ','
        """
        return self.tokenizer.symbol() == ','

    def _check_if_statement(self):
        """
        checks if we are currently compiling a statement
        :return: true iff the current token
        is in ['let', 'if', 'while', 'do', 'return']
        """
        return self.tokenizer.key_word() in STATEMENTS

    def _check_write_type(self):
        """
        checks if the current token is a valid type and if so, it writes it
        to  the output file
        """
        if self.tokenizer.key_word() in TYPE_KEYWORDS:
            self._write_token(self.tokenizer.token_type())
        else:
            self._check_write_name()

    def _check_write_symbol(self, expected_symbol):
        """
        checks if the current token is the expected symbol, if so it write
        it to the output file
        :param expected_symbol: the symbol we are validating is the current
        token
        :return: prints illegal statement error if it is not the expected
        symbol and exits the program
        """
        if self.tokenizer.symbol() != expected_symbol:
            print(ILLEGAL_STATEMENT_ERROR)
            sys.exit()
        self._write_token(self.tokenizer.token_type())

    def _check_write_name(self):
        """
        checks the current token is a name (identifier), and if so, write
        it to the output file
        :return: prints illegal statement error if it is not a name and
        exits the program
        """
        if self.tokenizer.identifier():
            self._write_token("IDENTIFIER")
        else:
            print(ILLEGAL_STATEMENT_ERROR)
            sys.exit()

    def _write_outer_tag(self, tag_str, end=False):
        """
        writes the outer tags of the different sections we are compiling
        :param tag_str: the string of the current section we are compiling
        :param end: true iff it is an end tag
        """
        if end:  # we decrease the indent count before the closing tag
            self._indent_count -= 1
            self.out_file.write("\t" * self._indent_count)
            self.out_file.write("</" + tag_str + ">\n")
        else:  # we increase the indent count after the opening tag
            self.out_file.write("\t" * self._indent_count)
            self.out_file.write("<" + tag_str + ">\n")
            self._indent_count += 1

    def _write_op(self):
        """
        writes an op symbol to the out file
        """
        self.out_file.write("\t" * self._indent_count)
        self.out_file.write("<symbol> ")
        if self.tokenizer.symbol() == '<':
            self.out_file.write("&lt;")
        elif self.tokenizer.symbol() == '>':
            self.out_file.write("&gt;")
        elif self.tokenizer.symbol() == '&':
            self.out_file.write("&amp;")
        elif self.tokenizer.symbol() == '\"':
            self.out_file.write("&quot;")
        else:
            self.out_file.write(self.tokenizer.symbol())
        self.out_file.write(" </symbol>\n")
        self.tokenizer.advance()

    def _write_token(self, cur_type):
        """
        writes the current token to the output file
        :param cur_type: the type of the current token
        """
        self.out_file.write("\t" * self._indent_count)
        self.out_file.write("<" + TOKEN_TYPE_STR[cur_type] + "> ")
        self.out_file.write(str(self.tokenizer.get_token_str()))
        self.out_file.write(" </" + TOKEN_TYPE_STR[cur_type] + ">\n")
        self.tokenizer.advance()
