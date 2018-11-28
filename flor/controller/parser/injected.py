#!/usr/bin/env python3
from flor.context.struct import Struct

# TODO: OUT-OF-CORE. Log could potentially be very big

class StructuredLog:

    def __init__(self):

        # self.log_sequence = None
        self.log_tree = None
        self.dict_of_returns = {}
        self.parents = []

    def lossless_compress(self):
        if 'log_sequence' in self.log_tree:
            queue = [self.log_tree['log_sequence'], ]
            parents = [self.log_tree, ]
            while queue:
                log_sequence = queue.pop(0)
                parent = parents.pop(0)
                filtered_log_sequence = list(filter(lambda x: 'block_type' not in x or 'log_sequence' in x, log_sequence))
                for log_seq_mem in filtered_log_sequence:
                    if 'block_type' in log_seq_mem:
                        # This log record is a block
                        queue.append(log_seq_mem['log_sequence'])
                        parents.append(log_seq_mem)
                    else:
                        # This is a proper log record
                        if 'in_file' not in parent:
                            parent['in_file'] = log_seq_mem['in_file']

                        if not log_seq_mem['from_arg']:
                            del log_seq_mem['from_arg']

                        del log_seq_mem['in_execution']
                        del log_seq_mem['in_file']

                        try:
                            x = eval(log_seq_mem['value'])
                            if x == log_seq_mem['runtime_value']:
                                del log_seq_mem['value']
                        except:
                            pass

                        for k in [each for each in log_seq_mem.keys()]:
                            if log_seq_mem[k] is None:
                                del log_seq_mem[k]

                parent['log_sequence'] = filtered_log_sequence




structured_log = StructuredLog()

class FlorEnter:
    pass

class FlorExit:
    pass

def internal_log(v, d):
    """
    Creates a new LOG_RECORD
    :param v:
    :param d:
    :return:
    """
    d['runtime_value'] = v
    # struct = Struct.from_dict(d)
    structured_log.log_tree['log_sequence'].append(d)
    return v

def log_enter(locl=None, vararg=None, kwarg=None):
    """
    Signals the entry of a BLOCK_NODE
    :param locl: a call to locals(). A dictionary mapping name to value of input args to a function
    :param vararg:
    :param kwarg:
    :return:
    """
    structured_log.parents.append(structured_log.log_tree)
    structured_log.log_tree = {}

    varargs = []
    kwargs = []

    consumes = False
    consumes_from = None

    if locl is not None:
        if vararg is not None:
            varargs = list(locl[vararg])
            del locl[vararg]
        if kwarg is not None:
            kwargs = list(locl[kwarg].values())
            del locl[kwarg]

        for arg in list(locl.values()) + varargs + kwargs:
            for returned_value in structured_log.dict_of_returns:
                func_names = structured_log.dict_of_returns[returned_value]
                consumes = returned_value is arg
                if type(returned_value) == list or type(returned_value) == tuple:
                    consumes = consumes or any([x is arg for x in returned_value])
                if consumes:
                    consumes_from = list(set(["{}".format(each) for each in func_names]))
                    break
            if consumes_from:
                break

    structured_log.log_tree['block_type'] = ''

    if consumes_from:
        structured_log.log_tree["consumes_from"] = consumes_from

    structured_log.log_tree['log_sequence'] = []




def log_exit(v=None, func_name=None):
    """
    Signals the exit of a BLOCK_NODE
    :param v:
    :param func_name:
    :return:
    """

    if func_name:
        # Return Context
        if v in structured_log.dict_of_returns:
            structured_log.dict_of_returns[v] |= {func_name,}
        else:
            structured_log.dict_of_returns[v] = {func_name,}

        structured_log.log_tree['block_type'] = "function_body :: {}".format(func_name)
    else:
        structured_log.log_tree['block_type'] = "loop_body"

    if not structured_log.log_tree['log_sequence']:
        del structured_log.log_tree['log_sequence']

    parent = structured_log.parents.pop()
    if parent:
        child = structured_log.log_tree
        structured_log.log_tree = parent

        structured_log.log_tree['log_sequence'].append(child)

    return v