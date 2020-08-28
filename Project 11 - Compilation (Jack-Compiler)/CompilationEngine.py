import sys
from JackTokenizer import *
from SymbolTable import *
from VMWriter import *

END_WHILE = True

ILLEGAL_STATEMENT_ERROR = "illegal statement"

CLASS_TAG = "class"

COMPILE_CLASS_ERROR = "invalid input in compile class"

COMPILE_TERM_ERROR = "invalid input in compile term"

CLASS_VAR_KEYWORDS = ['static', 'field']

TYPE_KEYWORDS = ['int', 'char', 'boolean']

SUBROUTINE = ['constructor', 'function', 'method']

UNARY_OPS = ['-', '~', '+', '*', '/']

KEYWORD_CONST = ['true', 'false', 'null', 'this']

STATEMENTS = ['let', 'if', 'while', 'do', 'return']

OPERATIONS = ['+', '-', '=', '>', '<', "*", "/", "&", "|", '~']


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
        self._tokenizer = JackTokenizer(in_file)
        self._class_table = SymbolTable()
        self._method_table = SymbolTable()
        self._cur_class_name = ""
        self._vm_writer = VMWriter(out_file)
        self._label_count_while = 0
        self._label_count_if = 0

    def compile_class(self):
        """
        compiles a class according to the grammar
        """
        self._class_table.start_subroutine()
        self._tokenizer.advance()
        # check if the current keyword is the right class tag
        if self._tokenizer.key_word() != CLASS_TAG:
            print(COMPILE_CLASS_ERROR)
            sys.exit()
        self._tokenizer.advance()
        self._cur_class_name = self.get_cur_token()
        self._tokenizer.advance()
        self._check_symbol("{")

        # there may be multiple variable declarations
        while self._check_if_var_dec():
            self.compile_class_var_dec()
        # there may be multiple subroutine declarations
        while self._check_subroutine_dec():
            self.compile_subroutine_dec()
        self._check_symbol("}")

    def compile_class_var_dec(self):
        """
        compiles the class's variables declarations
        """

        cur_kind = self.get_cur_token()
        self._tokenizer.advance()
        cur_type = self.get_cur_token()
        self._check_type()
        cur_name = self.get_cur_token()
        self._check_name()
        self._class_table.define(cur_name, cur_type, cur_kind)
        while self._check_if_comma():  # there are more variables
            self._tokenizer.advance()
            cur_name = self.get_cur_token()
            self._check_name()
            self._class_table.define(cur_name, cur_type, cur_kind)

        self._check_symbol(";")

    def get_cur_token(self):
        return self._tokenizer.get_token_str()

    def compile_subroutine_dec(self):
        """
        compiles the class's subroutine (methods and functions) declarations
        """
        # re-initialize the method symbol table
        self._method_table.start_subroutine()
        key_word = self._tokenizer.key_word()
        self._tokenizer.advance()
        self._tokenizer.advance()
        cur_name = self.get_cur_token()
        self._tokenizer.advance()

        # method get the as argument the base address of the current object
        if key_word == "method":
            self._method_table.define("this", self._cur_class_name, "argument")

        self._check_symbol("(")
        self.compile_parameter_list()
        self._check_symbol(")")

        subroutine_path = self._cur_class_name + '.' + cur_name
        # the function is either void or has a type

        self.compile_subroutine_body(subroutine_path, key_word)

    def compile_parameter_list(self):
        """
        compiles the parameter list for the subroutines
        """

        # if curr_token is ')' it means the param list is empty
        if self._tokenizer.symbol() == ')':
            return
        cur_type = self.get_cur_token()
        self._check_type()
        cur_name = self.get_cur_token()
        self._check_name()
        self._method_table.define(cur_name, cur_type, "argument")
        while self._check_if_comma():  # there are more params
            self._tokenizer.advance()
            cur_type = self.get_cur_token()
            self._check_type()
            cur_name = self.get_cur_token()
            self._check_name()
            self._method_table.define(cur_name, cur_type, "argument")

    def compile_subroutine_body(self, subroutine_name, subroutine_kind):
        """
        compiles the body of the subroutine
        """
        self._check_symbol("{")
        # there may be multiple variable declarations at the beginning of
        # the subroutine
        while self._tokenizer.key_word() == 'var':
            self.compile_var_dec()
        # define the subroutine
        n_locals = self._method_table.var_count("local")
        self._vm_writer.write_function(subroutine_name, n_locals)

        if subroutine_kind == "constructor":
            # allocating memory for the object's fields
            num_of_fields = self._class_table.var_count("field")
            self._vm_writer.write_push("constant", num_of_fields)
            self._vm_writer.write_call("Memory.alloc", 1)
            # make 'this' to point to address returned by Memory.alloc
            self._vm_writer.write_pop("pointer", 0)

        if subroutine_kind == "method":
            # assign pointer[0] to the object's base address in order to
            # get access to 'this' segment
            self._vm_writer.write_push("argument", 0)
            self._vm_writer.write_pop("pointer", 0)

        self.compile_statements()
        self._check_symbol("}")

    def compile_var_dec(self):
        """
        compiles the variable declarations
        """
        self._tokenizer.advance()
        cur_type = self.get_cur_token()
        self._check_type()
        cur_name = self.get_cur_token()
        self._check_name()
        self._method_table.define(cur_name, cur_type, "local")
        # there may be multiple variable names in the dec
        while self._check_if_comma():
            self._tokenizer.advance()
            self._method_table.define(self.get_cur_token(), cur_type, "local")
            self._check_name()
        self._check_symbol(";")

    def compile_statements(self):
        """
        compiles the statements (0 or more statements)
        """
        while self._check_if_statement():
            if self._tokenizer.key_word() == 'let':
                self.compile_let()
            elif self._tokenizer.key_word() == 'if':
                self.compile_if()
            elif self._tokenizer.key_word() == 'while':
                self.compile_while()
            elif self._tokenizer.key_word() == 'do':
                self.compile_do()
            elif self._tokenizer.key_word() == 'return':
                self.compile_return()

    def compile_do(self):
        """
        compiles the do statement
        """
        self._tokenizer.advance()
        self.compile_subroutine_call()
        self._check_symbol(";")
        self._vm_writer.write_pop("temp", 0)

    def compile_let(self):
        """
        compiles the let statement
        """
        self._tokenizer.advance()
        name = self.get_cur_token()
        info = self._get_symbol_info(name)
        self._check_if_declared(info)
        s_type, s_kind, s_id = info
        seg = self._get_segment(s_kind)
        is_and_array = False

        if self._tokenizer.get_next_token() == '[':  # if there is an array
            is_and_array = True
            self.compile_term()
        else:
            self._tokenizer.advance()
        self._check_symbol("=")
        self.compile_expression()

        if is_and_array:
            # save the value created after compiling the expression which
            # appears right after '=' in temp[0]
            self._vm_writer.write_pop("temp", 0)
            # now the top of the stack should be the address of the right cell
            # in the array so we assign it to pointer[1]
            self._vm_writer.write_pop("pointer", 1)
            # re-pushing the value we saved in temp[0]
            self._vm_writer.write_push("temp", 0)
            # the value of the array is located in that[0]
            seg = "that"
            s_id = 0
        # execute the assignment
        self._vm_writer.write_pop(seg, s_id)
        self._check_symbol(";")

    @staticmethod
    def _check_if_declared(info):
        if info is None:
            print("Unknown Symbol")
            sys.exit()

    def compile_if(self):
        """
        compiles the if statements
        """
        false_label = self._get_if_label()
        end_label = self._get_if_label()

        self._tokenizer.advance()
        self._check_symbol("(")
        self.compile_expression()
        self._check_symbol(")")
        self._check_symbol("{")
        self._vm_writer.write_arithmetic("not")
        self._vm_writer.write_if_goto(false_label)
        self.compile_statements()
        self._check_symbol("}")
        # there can also be an if else scenario
        self._vm_writer.write_goto(end_label)
        self._vm_writer.write_label(false_label)

        if self._tokenizer.key_word() == 'else':
            self._tokenizer.advance()
            self._check_symbol("{")
            self.compile_statements()
            self._check_symbol("}")

        self._vm_writer.write_label(end_label)

    def compile_while(self):
        """
        compiles the while statements
        """
        self._tokenizer.advance()
        first_label = self._get_while_label()
        second_label = self._get_while_label(END_WHILE)
        self._check_symbol("(")
        self._vm_writer.write_label(first_label)
        self.compile_expression()
        self._vm_writer.write_arithmetic("not")
        self._vm_writer.write_if_goto(second_label)
        self._check_symbol(")")
        self._check_symbol("{")
        self.compile_statements()
        self._vm_writer.write_goto(first_label)
        self._vm_writer.write_label(second_label)
        self._check_symbol("}")

    def compile_return(self):
        """
        compiles the return statements
        """
        self._tokenizer.advance()
        # if cur token is ; we return nothing, otherwise we return something
        if not self._tokenizer.symbol() == ';':
            self.compile_expression()
        else:
            self._vm_writer.write_push("constant", 0)
        self._check_symbol(";")
        self._vm_writer.write_return()

    def compile_subroutine_call(self):
        """
        compiles the subroutine calls ( when we actually call a subroutine
        as  opposed to declaring it)
        """
        method_name = self.get_cur_token()
        self._check_name()
        num_of_args = 0
        # there may be a '.' if it is a foo.bar() scenario (or Foo.bar())

        if self._tokenizer.symbol() == ".":

            self._tokenizer.advance()
            class_name = method_name
            method_name = self.get_cur_token()
            self._check_name()
            symbol_info = self._get_symbol_info(class_name)

            if symbol_info is None:
                cur_name = class_name + '.' + method_name
            else:
                type_of, kind_of, id_of = symbol_info
                num_of_args += 1
                self._vm_writer.write_push(self._get_segment(kind_of), id_of)
                cur_name = type_of + '.' + method_name
        else:
            cur_name = self._cur_class_name + '.' + method_name
            num_of_args += 1
            self._vm_writer.write_push("pointer", 0)

        self._check_symbol("(")
        num_of_args += self.compile_expression_list()
        self._check_symbol(")")
        self._vm_writer.write_call(cur_name, num_of_args)

    def compile_expression(self):
        """
        compiles expressions which are terms and possibly operators and more
        terms
        """
        symbol = self._tokenizer.symbol()
        self.compile_term()
        # write the 'not' operator if necessary
        if symbol == '~':
            self._vm_writer.write_arithmetic("not")

        # there may be a few operators in one expression
        while self._tokenizer.symbol() in OPERATIONS:
            symbol = self._tokenizer.symbol()
            self.compile_term()
            # executing operators after handling the the operands
            # in order to evaluate the current expression as postfix expression
            op = self._get_op(symbol)
            self._vm_writer.write_arithmetic(op)

    def compile_term(self):
        """
        compiles terms according to the grammar
        """
        cur_type = self._tokenizer.token_type()
        key_word = self._tokenizer.key_word()
        cur_token = self.get_cur_token()

        # either a string/int constant
        if cur_type in ["INT_CONST", "STRING_CONST"]:
            self._compile_string_int_term(cur_token, cur_type)

        # or a constant keyword (true, false, null, this)
        elif key_word in KEYWORD_CONST:
            self._compile_const_keyword_term(key_word)

        # or an expression within brown brackets
        elif self._tokenizer.symbol() == '(':
            self._tokenizer.advance()
            self.compile_expression()
            self._check_symbol(")")

        # or a unary op and then a term
        elif self._tokenizer.symbol() in OPERATIONS:

            self._tokenizer.advance()
            self.compile_term()

        # or it is an identifier which could be:
        elif self._tokenizer.identifier():
            self._compile_term_identifier()
        else:
            print(COMPILE_TERM_ERROR)
            sys.exit()

    def _compile_const_keyword_term(self, key_word):
        """
       compile term in case the current token type is constant keyword
       :param key_word: string from {'true', 'false', 'null', 'this'}
       """
        if key_word == "this":
            self._vm_writer.write_push("pointer", 0)
        else:
            self._vm_writer.write_push("constant", 0)
        if key_word == "true":
            self._vm_writer.write_arithmetic("not")
        self._tokenizer.advance()

    def _compile_string_int_term(self, cur_token, cur_type):
        """
        compile term in case the given token type is constant string
        or constant integer
        :param cur_token: the current token as a string
        :param cur_type:  the type of the current token
        """
        if cur_type == "INT_CONST":
            self._vm_writer.write_push("constant", cur_token)

        else:  # is string
            n = len(cur_token)
            self._vm_writer.write_push("constant", n)
            self._vm_writer.write_call("String.new", 1)
            for c in cur_token:
                self._vm_writer.write_push("constant", ord(c))
                self._vm_writer.write_call("String.appendChar", 2)
        self._tokenizer.advance()

    def _compile_term_identifier(self):
        """
         compiles terms in case of identifier token
        """
        cur_token = self.get_cur_token()
        info = self._get_symbol_info(cur_token)
        next_token = self._tokenizer.get_next_token()
        if info is not None and next_token not in [".", "("]:
            type_of, kind_of, id_of = info
            seg = self._get_segment(kind_of)
            self._vm_writer.write_push(seg, id_of)

        # an array
        if next_token == '[':

            self._check_name()
            self._check_symbol("[")
            self.compile_expression()
            self._check_symbol("]")
            self._vm_writer.write_arithmetic("add")
            if self._tokenizer.symbol() != '=':
                self._vm_writer.write_pop("pointer", 1)
                self._vm_writer.write_push("that", 0)
        # or a subroutine call
        elif next_token in [".", "("]:
            self.compile_subroutine_call()
        else:
            self._tokenizer.advance()

    def compile_expression_list(self):
        """
        compiles the expression lists
        """
        # if it is ')' then the expression list is empty
        if self._tokenizer.symbol() == ')':
            return 0
        num_of_args = 1  # at least one argument
        self.compile_expression()
        # while there are more expressions
        while self._check_if_comma():
            self._tokenizer.advance()
            cur_symbol = self._tokenizer.symbol()
            self.compile_expression()
            if cur_symbol == '-':  # negative int
                self._vm_writer.write_arithmetic("neg")
            num_of_args += 1
        return num_of_args

    def _check_if_var_dec(self):
        """
        check if we are currently compiling a variable declaration
        :return: true iff the current token is either 'static' or 'field'
        """
        return self._tokenizer.key_word() in CLASS_VAR_KEYWORDS

    def _check_subroutine_dec(self):
        """
        checks if we are currently compiling a subroutine declaration
        :return: true iff the current token is either 'constructor' or
        'function' or 'method'
        """
        return self._tokenizer.key_word() in SUBROUTINE

    def _check_if_comma(self):
        """
        checks if current token is a comma
        :return: true iff the current token is a ','
        """
        return self._tokenizer.symbol() == ','

    def _check_if_statement(self):
        """
        checks if we are currently compiling a statement
        :return: true iff the current token
        is in ['let', 'if', 'while', 'do', 'return']
        """
        return self._tokenizer.key_word() in STATEMENTS

    def _check_type(self):
        """
        checks if the current token is a valid type and if so, it writes it
        to  the output file
        """
        if not self._tokenizer.key_word() in TYPE_KEYWORDS:
            self._check_name()
        else:
            self._tokenizer.advance()

    def _check_symbol(self, expected_symbol):
        """
        checks if the current token is the expected symbol, if so it write
        it to the output file
        :param expected_symbol: the symbol we are validating is the current
        token
        :return: prints illegal statement error if it is not the expected
        symbol and exits the program
        """
        if self._tokenizer.symbol() != expected_symbol:
            print(ILLEGAL_STATEMENT_ERROR)
            sys.exit()
        self._tokenizer.advance()

    def _check_name(self):
        """
        checks the current token is a name (identifier), and if so, write
        it to the output file
        :return: prints illegal statement error if it is not a name and
        exits the program
        """
        if not self._tokenizer.identifier():
            print(ILLEGAL_STATEMENT_ERROR)
            sys.exit()
        self._tokenizer.advance()

    @staticmethod
    def _get_op(symbol):
        """
       writes an op symbol to the out file
       """
        if symbol == '<':
            return "lt"
        elif symbol == '>':
            return "gt"
        elif symbol == '=':
            return "eq"
        elif symbol == '&':
            return "and"
        elif symbol == '|':
            return "or"
        elif symbol == '+':
            return "add"
        elif symbol == '-':
            return "sub"
        elif symbol == '~':
            return "not"
        elif symbol == "*":
            return "call Math.multiply 2"
        elif symbol == "/":
            return "call Math.divide 2"

    def _get_symbol_info(self, symbol_name):
        """
        first checks if the given symbol in the method symbol table
        if the method table contains the symbol it returns it's information:
        (type,kind,id)
        otherwise check if the class symbol table contains the symbol
        if it does it return the symbol information from the class table
        else returns None
        :param symbol_name: string
        """
        info = self._method_table.get_info(symbol_name)
        if info is None:
            info = self._class_table.get_info(symbol_name)
        return info

    @staticmethod
    def _get_segment(cur_kind):
        """
        :param cur_kind: Jack kind - from the list:
         ["var", "argument", "field", "class", "subroutine", "local", "static"]
        :return: if the given kind is "field" it returns 'this'
        otherwise returns the given kind
        """
        if cur_kind == "field":
            return "this"
        else:
            return cur_kind

    def _get_if_label(self):
        """
        create new if label and increment the if label counter
        :return: if unused label
        """
        curr_counter = str(self._label_count_if)
        self._label_count_if += 1
        return "IF" + curr_counter

    def _get_while_label(self, is_end_while=False):
        """
        creates label according to the given flag, if the method creates
        end while label it increments the while label counter
        :param is_end_while: if true creates end while label
        otherwise creates while label
        :return: unused while label or end while label according to the flag
        """
        curr_counter = str(self._label_count_while)
        if is_end_while:
            self._label_count_while += 1
            return "WHILE_END" + curr_counter
        return "WHILE" + curr_counter
