import re

IS_EMPTY_LINE = ""

END_OF_FILE = ""

JACK_INT_RANGE = 32767

KEY_WORDS = {"class": "CLASS", "method": "METHOD", "function": "FUNCTION",
             "constructor": "CONSTRUCTOR",
             "int": "INT", "boolean": "BOOLEAN", "char": "CHAR",
             "void": "VOID", "var": "VAR", "static": "STATIC",
             "field": "FIELD", "let": "LET", "do": "DO", "if": "IF",
             "else": "ELSE", "while": "WHILE",
             "return": "RETURN", "true": "TRUE", "false": "FALSE",
             "null": "NULL", "this": "THIS"}

SYMBOLS = ["{", "}", "(", ")", "[", "]", ".", ",", ";", "+", "-", "*", "/",
           "&", "|", "<", ">", "=", "~"]
SYMBOLS_STR = "{}()\[\].,;+\-*/&|<>=~"
TOKEN_REGEX = r'(\".*\"|(?!\")[' + SYMBOLS_STR + '])|(?!\")[ \t]'
COMMENT_PATTERN = r'//.*?$|/\*.*?\*/|\'(?:\\.|[^\\\'])*\'|"(?:\\.|[^\\"])*"'
IDENTIFIER_PATTERN = "(\\s*(((_)[\\w])|[a-zA-Z])[\\w_]*\\s*)"
STRING_PATTERN = "\"[^\"]*\""


class JackTokenizer:

    def __init__(self, path):
        """
        A constructor for the JackTokenizer
        :param path: the path of the current input file we want to compile
        """
        self._file = open(path)
        self.curr_token = None
        self._within_comment = False
        self._token_buff = self._get_tokens()

    def _get_tokens(self):
        """
        reads the file line by line - for each line we create a list of tokens
        :return: list of tokens in the current line we are parsing in the
        input file
        """
        curr_line = self._file.readline()
        if not curr_line:
            return
        curr_line = self._handle_comments(curr_line).strip()
        curr_line = JackTokenizer.comment_remover(curr_line)
        tokens = re.split(TOKEN_REGEX, curr_line)
        return list(filter(None, tokens))

    def _handle_comments(self, curr_line):
        """
        we want to get rid of all the comments so we need to read lines until
        we reach the end of the comment
        :param curr_line: the current line we are reading
        :return: the current line after we are done with the comment
        """
        while self._check_if_to_skip(curr_line):
            curr_line = self._file.readline()
        return curr_line

    @staticmethod
    def comment_remover(text):
        """
        removes the comments from the line (sometimes there are comments
        after  code,we want to remove it but keep the code
        :param text: the current line
        :return: the current line without any comments
        """

        def replace_space(line):
            return " " if line.group(0).startswith('/') else line.group(0)

        pattern = re.compile(COMMENT_PATTERN, re.DOTALL | re.MULTILINE)
        return re.sub(pattern, replace_space, text)

    def _check_if_to_skip(self, curr_line):
        """
        check if the current line is white space or comment
        :param curr_line: the current line we are checking
        :return: true if white space or comment, false otherwise
        """
        if curr_line == END_OF_FILE:
            return False
        curr_line = curr_line.strip()
        if curr_line == IS_EMPTY_LINE:
            return True
        if curr_line.startswith("//"):
            return True
        if curr_line.startswith("/**") or curr_line.startswith("/*"):
            self._within_comment = True
        if self._within_comment and curr_line.endswith('*/'):
            self._within_comment = False
            return True
        return self._within_comment

    def get_next_token(self):
        """
        gets the next token (the one after the current token)
        :return: the next token (which is at the beginning of our token buff)
        """
        if self._token_buff:
            return self._token_buff[0]

    def has_more_tokens(self):
        """
        checks if there are any more tokens left in the file we are reading
        by checking if our token buffer is empty or not
        :return: false iff the token buff is empty meaning there are no more
        tokens
        """
        if self._token_buff:
            return len(self._token_buff) > 0

    def advance(self):
        """
        we pop the first token in our token buffer to be the current token,
        if the token buffer is now empty we read another line from the file
        and fill the token buff with tokens from the new line
        """
        if not self.has_more_tokens():
            self._file.close()
            return
        self.curr_token = self._token_buff.pop(0)
        if not self.has_more_tokens():
            self._token_buff = self._get_tokens()

    def token_type(self):
        """
        a getter for the current token's type
        :return: the type of the current token
        """
        if not self.curr_token:
            return "No current token"
        if self._is_keyword():
            return "KEYWORD"
        elif self._is_symbol():
            return "SYMBOL"
        elif self._is_int():
            return "INT_CONST"
        elif self._is_str():
            return "STRING_CONST"
        elif self._is_identifier():
            return "IDENTIFIER"

    def _is_symbol(self):
        """
        :return: true if the curr_token is a symbol and false otherwise
        """
        return self.curr_token in SYMBOLS

    def _is_keyword(self):
        """
        :return: true if the curr_token is a keyword and false otherwise
        """
        return self.curr_token in KEY_WORDS

    def _is_int(self):
        token = self.curr_token
        return token.isdigit() and int(token) in range(JACK_INT_RANGE)

    def _is_str(self):
        """
        :return: true if the curr_token is a int and false otherwise
        """
        return re.match(STRING_PATTERN, self.curr_token)

    def _is_identifier(self):
        """
        :return: true if the curr_token is a identifier and false otherwise
        """
        return re.match(IDENTIFIER_PATTERN, self.curr_token)

    def key_word(self):
        """
        :return: the current token string if the current token is a key_word
        """
        if self._is_keyword():
            return self.curr_token

    def symbol(self):
        """
        :return: the current token string if the current token is a symbol
        """
        if self._is_symbol():
            return self.curr_token

    def identifier(self):
        """
        :return: the current token string if the current token is an identifier
        """
        if self._is_identifier():
            return self.curr_token

    def int_val(self):
        """
        :return: the current token int if the current token is an int
        """
        if self._is_int():
            return int(self.curr_token)

    def string_val(self):
        """
        :return: the current token string if the current token is a string
        """
        if self._is_str():
            return self.curr_token.replace("\"", "")

    def get_token_str(self):
        """
        a getter for the string of the current token - no matter what the
        type is
        :return: a string of the current token
        """
        curr_type = self.token_type()
        if curr_type == "KEYWORD":
            return self.key_word()
        if curr_type == "SYMBOL":
            return self.symbol()
        if curr_type == "IDENTIFIER":
            return self.identifier()
        if curr_type == "INT_CONST":
            return self.int_val()
        if curr_type == "STRING_CONST":
            return self.string_val()
