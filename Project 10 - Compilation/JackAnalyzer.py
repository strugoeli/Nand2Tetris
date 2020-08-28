#!/bin/bash
import os
from CompilationEngine import *

INVALID_INPUT_ERROR = "Invalid input file"

NUM_OF_ARG = 2
ARG_ERROR = "Wrong Number of args"


class JackAnalyzer:
    """
    The Jack analyzer class runs the show
    """

    def __init__(self, path):
        """
        constructor for the Jack Analyzer
        :param path: the path of the file / directory we wish to compile
        """
        self._in_path = path
        self._out_path = path
        self._inputs = self._get_paths()

    def create_out(self):
        """
        creates the output files - first we get the output file name and
        then  we create a compilation engine with our in file and out file
        and the engine compiles the infile and saves the output in
        the output file
        """
        for file in self._inputs:
            out_name = str(os.path.basename(file).split('.')[0]) + ".xml"
            comp = CompilationEngine(file, self._out_path + "/" + out_name)
            comp.compile_class()

    def _get_paths(self):
        """
        gets the file paths from the initial input path
        """
        res = []
        if os.path.isdir(self._in_path):
            if self._in_path.endswith("/"):
                self._in_path = self._in_path[0:-1]
            files = os.listdir(self._in_path)
            gen = (file for file in files if file.endswith('.jack'))
            for file in gen:
                res.append(self._in_path + '/' + file)
        elif os.path.isfile(self._in_path):
            self._out_path = os.path.dirname(self._in_path)
            res.append(self._in_path)
        else:
            print(INVALID_INPUT_ERROR)
            sys.exit()
        return res


if __name__ == '__main__':
    if len(sys.argv) != NUM_OF_ARG:
        print(ARG_ERROR)
        sys.exit()
    current_input = sys.argv[1]
    analyzer = JackAnalyzer(current_input)
    analyzer.create_out()
