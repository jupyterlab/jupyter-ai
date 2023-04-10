from IPython.core.magic import register_line_magic
from IPython.core.getipython import get_ipython
from IPython.core.ultratb import ListTB

import traceback

def store_exception(shell, etype, evalue, tb, tb_offset=None):
    # Model the exception in plain text
    if tb:
        etb = traceback.extract_tb(tb).format()
        estring = '\n'.join(etb)
    else:
        etb = None
        estring = None

    styled_exception = ('Exception type: ' + str(etype.__name__) +
        '\nException value: ' + str(evalue) +
        '\nTraceback: ' + estring)

    prompt_number = shell.execution_count
    err = shell.user_ns.get("Err", {})
    err[prompt_number] = styled_exception
    shell.user_ns["Err"] = err
    
    # Return structured traceback, a list of strings, or None
    return shell.showtraceback()
