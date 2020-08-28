#!/usr/bin/env python3

import os
import sys
import re

SEG_TO_RESTORE = ["THAT", "THIS", "ARG", "LCL"]

WRONG_COMMAND = "Invalid command"

NO_SUCH_FILE_ERROR = "There is no such file: "
ARG_ERROR = "Illegal number of arguments "
REGEX = "^(?:(?!\/\/).)*[a-zA-Z0-9]+"
RETURN_TYPE = "C_RETURN"
NUM_OF_ARG = 2
SECOND_ARG = 2
FIRST_ARG = 1
INVALID_TYPE = ""
NO_COMMAND = -1
BINARY = 0
UNARY = 1
BOOL = 2


class Parser:
    """
    parses each VM command into it's lexical elements
    """
    BINARY_T = {"C_PUSH", "C_POP", "C_FUNCTION", "C_CALL"}
    ARITHMETIC_T = {"add", "sub", "neg", "eq", "and", "or", "not", "gt", "lt"}

    def __init__(self, file):
        """
        the parser constructor
        :param file: the file we wish to parse
        """
        self.__lines = []
        for line in open(file):
            curr_line = "".join(re.findall(REGEX, line))
            if curr_line:
                self.__lines.append(curr_line)
        self.__num_of_commands = len(self.__lines)
        self.__current_command = NO_COMMAND

    def has_more_commands(self):
        """
        boolean function that checks if there are more commands to parse
        :return: true iff there are more commands to parse
        """
        return self.__current_command < self.__num_of_commands - 1

    def advance(self):
        """
        increments the current command counter every time we parse a command
        :return: if there are no more commands
        """
        if not self.has_more_commands():
            return
        self.__current_command += 1

    def command_type(self):
        """
        gets the command type
        :return: "C_ARITHMETIC" if arithmetic, "C_PUSH/POP" if push/pop
        """
        curr_arg1 = self.__lines[self.__current_command].split(' ', 1)[0]
        if curr_arg1 in Parser.ARITHMETIC_T:
            return "C_ARITHMETIC"
        if curr_arg1 == "push":
            return "C_PUSH"
        elif curr_arg1 == "pop":
            return "C_POP"
        else:
            return curr_arg1

    def arg1(self):
        """
        returns the first argument of the current command. in the case of
        C ARITHMETIC the command itself (add, sub etc.), is returned.
        :return: a string of the first argument of the current command
        """
        curr_line = self.__lines[self.__current_command]
        if curr_line == RETURN_TYPE:
            return INVALID_TYPE
        if curr_line in Parser.ARITHMETIC_T:
            return curr_line
        return curr_line.split(' ', 2)[FIRST_ARG]

    def arg2(self):
        """
        returns the second argument of the current command
        :return: int (the index argument of the command)
        """
        if self.command_type() in Parser.BINARY_T or self.command_type() in ["function", "call"]:
            return self.__lines[self.__current_command].split(' ', 2)[SECOND_ARG]
        else:
            return INVALID_TYPE

    def get_curr_line(self):
        """
        gets the current line we are parsing
        :return: the current line
        """
        return self.__lines[self.__current_command]


class CodeWriter(object):
    """
    generates assembly code from the parsed VM command
    """

    def __init__(self, output_file_name):
        """
        a CodeWriter constructor
        :param output_file_name: the output filename we wish to write to
        """
        self.output_asm = open(output_file_name, 'w')
        self.current_file = ""
        self._bool_counter = 0
        self._return_counter = 0
        self._operators = self._init_operators()
        self._addresses = self._init_addresses()
        self.function_name = "Sys.init"
        self.write_init()

    def write_init(self):
        """
        initializes the stack pointer to 256 and calls Sys.init
        """
        self._write("\n//INIT\n")

        self._write("@256")
        self._write("D=A")
        self._write("@SP")
        self._write("M=D")
        self.write_call("Sys.init", 0)

    def write_label(self, label):
        """
        writes the assembly code that is the translation of the label command
        :param label: a string label
        """
        self._write("(" + self.function_name + "$" + label + ")")

    def write_goto(self, label):
        """
        writes the assembly code that is the translation of the goto command
        :param label: a string label
        """
        self._write("@" + self.function_name + "$" + label)
        self._write("0;JMP  // goto " + label)
        return

    def write_if(self, label):
        """
        writes the assembly code that is the translation of the if-goto command
        :param label: a string label
        """
        self._write("\n//IF\n")
        self._pop_stack()
        self._write("@" + self.function_name + "$" + label)
        self._write("D;JNE  // if true go to " + label)

    def _update_stack_address(self, address):
        self._write("@" + address)
        self._write("D=M")
        self._push_to_stack()

    def _update_stack_const(self, val):
        self._write("@" + val)
        self._write("D=A")
        self._push_to_stack()

    def write_call(self, func_name, nargs):
        """
        writes the assembly code that is the translation of the call command
        :param func_name: string (the function name)
        :param nargs: the number of arguments that we call the command with
        """
        self._write("\n//Call Function\n")

        return_add = func_name + "$ret." + str(self._return_counter)
        self._update_stack_const(return_add)

        self._update_stack_address("LCL")
        self._update_stack_address("ARG")
        self._update_stack_address("THIS")
        self._update_stack_address("THAT")

        self._write("@SP")
        self._write("D=M")
        arg_num = 5 + int(nargs)
        self._write("@" + str(arg_num))
        self._write("D=D-A")
        self._write("@ARG")
        self._write("M=D")

        self._write("@SP")
        self._write("D=M")
        self._write("@LCL")
        self._write("M=D")

        self._write("@" + func_name)
        self._write("0;JMP")
        self._write("(" + return_add + ")")

        self._return_counter += 1

    def write_return(self):
        """
        writes the assembly code that is the translation of the return command
        """
        self._write("\n//Return\n")

        self._write("@LCL")
        self._write("D=M")
        self._write("@R14")  # endFrame =LCL
        self._write("M=D")

        self._write("@5")
        self._write("A=D-A")
        self._write("D=M")  # retAddress =*(endFrame -5)
        self._write("@R15")
        self._write("M=D")

        self._pop_stack()
        self._write("@ARG")
        self._write("A=M")  # *ARG = pop()
        self._write("M=D")

        self._write("@ARG")
        self._write("D=M")  # SP = ARG +1
        self._write("@SP")
        self._write("M=D+1")

        for seg in SEG_TO_RESTORE:
            self.get_prev_data()
            self._write("@" + seg)
            self._write("M=D")

        self._write("@R15")
        self._write("A=M")  # goto returnAddress
        self._write("0;JMP")

    def get_prev_data(self):
        self._write("@R14")
        self._write("M=M-1")
        self._write("A=M")
        self._write("D=M")

    def write_function(self, func_name, n_locals):
        """
        writes the assembly code that is the translation of the given function command
        :param func_name: a string (the function name)
        :param n_locals: an int (the number of local variables in the function)
        """
        self.function_name = func_name
        self._write("(" + func_name + ")")

        for i in range(int(n_locals)):
            self._update_stack_const("0")

    def write_arithmetic(self, command, line):
        """
        writes to the output file the assembly code that implements the given
        arithmetic command
        :param command: an operator
        :param line: the line we are currently translating (for comment)
        """
        self._write("\n// " + line)
        if command in self._operators[BINARY]:  # Binary operator
            self.handle_binary_op(command)

        elif command in self._operators[UNARY]:
            self.handle_unary_op(command)

        elif command in self._operators[BOOL]:  # Boolean operators
            self.handle_boolean_op(command)
        else:
            print(WRONG_COMMAND)
            sys.exit()

        self._increment_sp()

    def write_push_pop(self, command, segment, index, line):
        """
        writes to the output file the assembly code that implements the
        given command, where command is either C_PUSH or C_POP
        :param command: either C_PUSH or C_POP
        :param segment: string
        :param index: int
        :param line: current line we are translating (for comment)
        """
        self._write("\n// " + line)
        self._write_address(segment, index)
        if command == 'C_PUSH':  # we want to load M[address] to D
            if segment == 'constant':
                self._write('D=A')
            else:
                self._write('D=M')
            self._push_to_stack()
        elif command == 'C_POP':  # we want to load D to M[address]
            self._write('D=A')
            self._write('@R13')  # keep address in R13
            self._write('M=D')
            self._pop_stack()
            self._write('@R13')
            self._write('A=M')
            self._write('M=D')
        else:
            print(WRONG_COMMAND)
            sys.exit()

    def handle_boolean_op(self, command):
        """
        writes the boolean operation while preventing stack overflow
        :param command: the boolean operator
        """
        self._pop_stack()
        self._write('@R13')  # keep address in R13
        self._write('M=D')
        self._write('@CASE_Y_NEG{}'.format(self._bool_counter))
        self._write('D;JLT')
        self._pop_stack()
        self._write('@CASE_X_NEG_Y_POS{}'.format(self._bool_counter))
        self._write('D;JLT')
        self._write('@R13')
        self._write('D=D-M')
        self._write('@CHECK{}'.format(self._bool_counter))
        self._write('0;JMP')
        self._write('(CASE_Y_NEG{})'.format(self._bool_counter))
        self._pop_stack()
        self._write('@CASE_Y_NEG_X_POS{}'.format(self._bool_counter))
        self._write('D;JGT')
        self._write('@R13')
        self._write('D=D-M')
        self._write('@CHECK{}'.format(self._bool_counter))
        self._write('0;JMP')
        self._write('(CASE_X_NEG_Y_POS{})'.format(self._bool_counter))
        self._write('D=-1')
        self._write('@CHECK{}'.format(self._bool_counter))
        self._write('0;JMP')
        self._write('(CASE_Y_NEG_X_POS{})'.format(self._bool_counter))
        self._write('D=1')
        self._write('@CHECK{}'.format(self._bool_counter))
        self._write('0;JMP')
        self._write('(CHECK{})'.format(self._bool_counter))
        self._write('@CORRECT{}'.format(self._bool_counter))
        self._write('D;' + self._operators[BOOL][command])
        self._write('D=0')
        self._write('@END{}'.format(self._bool_counter))
        self._write('0;JMP')
        self._write('(CORRECT{})'.format(self._bool_counter))
        self._write('D=-1')
        self._write('@END{}'.format(self._bool_counter))
        self._write('0;JMP')
        self._write('(END{})'.format(self._bool_counter))
        self._set_a_to_sp()
        self._write('M=D')
        self._bool_counter += 1

    def handle_unary_op(self, command):
        """
        writes the unary operation
        :param command: unary operator
        """
        self._decrement_sp()
        self._set_a_to_sp()
        self._write('M=' + self._operators[UNARY][command] + 'M')

    def handle_binary_op(self, command):
        """
        writes binary operation
        :param command: binary operator
        """
        self._pop_stack()
        self._decrement_sp()
        self._set_a_to_sp()
        self._write('M=M' + self._operators[BINARY][command] + 'D')

    def close(self):
        """
        closes the asm file
        """
        self.output_asm.close()

    @staticmethod
    def _init_operators():
        """
        :return: a list of our operator dictionaries
        """
        return [
            {  # binary operators
                'add': '+',
                'sub': '-',
                'and': '&',
                'or': '|'
            },
            {  # unary operators
                'neg': '-',
                'not': '!'
            },
            {  # bool operators
                'eq': 'JEQ',
                'gt': 'JGT',
                'lt': 'JLT'
            }
        ]

    @staticmethod
    def _init_addresses():
        """
        :return: a dictionary of our memory addresses for each segment
        """
        return {
            'local': 'LCL',
            'argument': 'ARG',
            'this': 'THIS',
            'that': 'THAT',
            'static': 16,
            'temp': 5,
            'pointer': 3
        }

    def update_current_filename(self, vm_file):
        """
        update current file name to be the name of the vm file we are
        translating
        :param vm_file: the vm file name we are currently translating
        """
        self.current_file = vm_file.split('.')[0]

    def _write(self, output_line):
        """
        writes the output line to the output file
        :param output_line: the line we are writing
        """
        out = output_line if '(' in output_line else '\t' + output_line
        self.output_asm.write(out + '\n')

    def _write_address(self, segment, index):
        """
        writes the address of the given segment in the output file
        :param segment: the current segment
        :param index: int
        """
        if segment == 'constant':
            # we write @index
            self._write('@' + str(index))
        elif segment == 'static':
            # we write @current_file.index (current_file is the name of
            # the vm file we are currently translating
            self._write('@' + self.current_file + '.' + str(index))
        elif segment in ['temp', 'pointer']:
            # we write @R and then the correct index which is the index the
            # segment initial address
            self._write('@R' + str(self._addresses[segment] + int(index)))
        elif segment in ['local', 'argument', 'this', 'that']:
            self._write('@' + self._addresses[segment])
            self._write('D=M')
            self._write('@' + str(index))
            self._write('A=D+A')
        else:
            print(WRONG_COMMAND)
            sys.exit()

    def _push_to_stack(self):
        """
        pushes current value of D register onto the stack and then
        increments stack pointer
        """
        self._set_a_to_sp()
        self._write('M=D')  # push the content of D onto the stack
        self._increment_sp()

    def _pop_stack(self):
        """
        first we decrement @SP and then we put the value at the top of the
        stack into D
        """
        self._decrement_sp()
        self._write('A=M')  # set A to current sp
        self._write('D=M')  # pop stack into D

    def _decrement_sp(self):
        """
        decrements stack pointer by 1
        """
        self._write('@SP')
        self._write('M=M-1')

    def _increment_sp(self):
        """
        increments stack pointer by 1
        """
        self._write('@SP')
        self._write('M=M+1')

    def _set_a_to_sp(self):
        """
        sets A register to be the stack pointer
        """
        self._write('@SP')
        self._write('A=M')


def translate_to_assembler(file, code_writer):
    """
    translates the vm file to an asm file by creating a parser
    and passing commands to our code writer
    :param file: the vm file we wish to translate
    :param code_writer: the code_writer object we created that corresponds
    to the file we are parsing
    """
    parser = Parser(file)
    while parser.has_more_commands():
        parser.advance()
        curr_type = parser.command_type()
        if curr_type in ["C_PUSH", "C_POP"]:
            code_writer.write_push_pop(curr_type, parser.arg1(), parser.arg2(),
                                       parser.get_curr_line())
        elif curr_type == "C_ARITHMETIC":
            code_writer.write_arithmetic(parser.arg1(), parser.get_curr_line())
        elif curr_type == "label":
            code_writer.write_label(parser.arg1())
        elif curr_type == "goto":
            code_writer.write_goto(parser.arg1())
        elif curr_type == "if-goto":
            code_writer.write_if(parser.arg1())
        elif curr_type == "function":
            code_writer.write_function(parser.arg1(), parser.arg2())
        elif curr_type == "call":
            code_writer.write_call(parser.arg1(), parser.arg2())
        else:
            code_writer.write_return()


def translate_dir(dir_path):
    """
    translates all the vm files in a given directory
    :param dir_path: the dearest of paths
    """
    if dir_path.endswith("/"):
        dir_path = dir_path[0:-1]
    files = os.listdir(dir_path)
    directory_name = os.path.basename(dir_path)
    output_name = dir_path + "/" + directory_name + ".asm"
    code_writer = CodeWriter(output_name)
    gen = (file for file in files if file.endswith('.vm'))
    for file in gen:
        code_writer.update_current_filename(file)
        translate_to_assembler(dir_path + "/" + file, code_writer)
    code_writer.close()


if __name__ == '__main__':

    if len(sys.argv) != NUM_OF_ARG:
        print(ARG_ERROR)
        sys.exit()
    current_input = sys.argv[1]
    if os.path.isdir(current_input):  # input is directory
        translate_dir(current_input)
    elif not os.path.isfile(current_input):  # no such file
        print(NO_SUCH_FILE_ERROR + current_input)
        sys.exit()
    else:  # input is single file
        file_name = current_input.split('.')[0]
        current_output = file_name + ".asm"
        code = CodeWriter(current_output)
        code.current_file = current_output
        translate_to_assembler(current_input, code)
        code.close()
