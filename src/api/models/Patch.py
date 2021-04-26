import jsonpatch


class Patch():
    REPLACE = "replace"
    ADD = "add"
    REMOVE = "remove"
    COPY = "copy"
    MOVE = "move"

    op = ""
    _from = ""
    path = ""
    value = ""

    def __init__(self, op, path, value):
        self.op = op
        self.path = path
        self.value = value
        return

    def __copy_move__(self, op, from_param, path):
        self.op = op
        self._from = from_param
        self.path = path
        return self
