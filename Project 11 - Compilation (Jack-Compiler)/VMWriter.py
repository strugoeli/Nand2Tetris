class VMWriter:

    def __init__(self, out_file):
        """
        Creates a new output.bm file and prepares it for writing
        :param out_file: output file/stream
        """
        self.out_file = open(out_file, 'w')

    def write_push(self, segment, index):
        """
        Writes a VM push command
        :param segment: string from {argument,local,static,this,that,
        pointer,temp}
        :param index: int
        """
        self.out_file.write("push " + segment + " " + str(index) + '\n')

    def write_pop(self, segment, index):
        """
        Writes a VM pop command
        :param segment: string from {argument,local,static,this,that,
        pointer,temp}
        :param index: int
        """
        self.out_file.write("pop " + segment + " " + str(index) + '\n')

    def write_call(self, name, n_args):
        """
        Writes a VM call command
        :param name: string
        :param n_args: int
        :return:
        """
        self.out_file.write("call " + name + " " + str(n_args) + '\n')

    def write_arithmetic(self, command):
        """
        Writes arithmetic-logical command
        :param command: from {add,sub,neg,not,eq,gt,lt,and,or}
        """
        self.out_file.write(command + '\n')

    def write_return(self):
        """
        Writes a VM return command
        """
        self.out_file.write("return\n")

    def write_goto(self, label_name):
        """
        Writes a VM goto command
        :param label_name: string
        """
        self.out_file.write("goto " + label_name + '\n')

    def write_if_goto(self, label_name):
        """
        Writes a VM if-goto command
        :param label_name: string
        """
        self.out_file.write("if-goto " + label_name + '\n')

    def write_label(self, label_name):
        """
        Writes a VM label command

        :param label_name: string
        """
        self.out_file.write("label " + label_name + '\n')

    def write_function(self, name, n_locals):
        """
        Writes a VM function command

        :param name:  string
        :param n_locals: number of locals(int)
        """
        self.out_file.write("function " + name + " " + str(n_locals) + '\n')

    def close(self):
        """
        closes the file
        """
        self.out_file.close()
