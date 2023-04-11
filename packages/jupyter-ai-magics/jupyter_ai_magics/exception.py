from IPython.core.magic import register_line_magic
from IPython.core.getipython import get_ipython
from IPython.core.ultratb import ListTB

import traceback

def store_exception(shell, etype, evalue, tb, tb_offset=None):
    # A structured traceback (a list of strings) or None
    stb = shell.InteractiveTB.structured_traceback(etype, evalue, tb, tb_offset=tb_offset)
    stb_text = shell.InteractiveTB.stb2text(stb)

    etraceback = shell.showtraceback()

    styled_exception = str(stb_text)

    prompt_number = shell.execution_count
    err = shell.user_ns.get("Err", {})
    err[prompt_number] = styled_exception
    shell.user_ns["Err"] = err
    
    # Return 
    return etraceback
