KINDS = ["var", "argument", "field", "class", "subroutine", "local", "static"]


class SymbolTable:

    def __init__(self):
        """
        creates new symbol table
        """
        self._table = dict()
        self._kind_num = dict()
        for kind in KINDS:
            self._kind_num[kind] = 0

    def define(self, cur_name, cur_type, cur_kind):
        """
         Defines a new identifier of the given arguments, and assigns it a
         running index
        :param cur_name: string
        :param cur_type: string
        :param cur_kind: one of : {static,field, argument ,var}
        """
        cur_id = self._kind_num[cur_kind]
        self._table[cur_name] = [cur_type, cur_kind, cur_id]
        self._kind_num[cur_kind] += 1

    def start_subroutine(self):
        """
        starts a new subroutine scope(i.e., resets the subroutine's symbol
        table)
        """
        self._table.clear()
        for x in KINDS:
            self._kind_num[x] = 0

    def var_count(self, kind):
        """
        :param kind: string
        :return:  the number of vars of the given kind already defiend in
        the current scope.
        """
        return self._kind_num[kind]

    def get_info(self, name):
        """
        :param name: name of the identifier
        :return: the information of the given identifier name
        type,kind and id
        """
        return self._table.get(name)
