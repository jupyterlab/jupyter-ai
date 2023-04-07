from IPython.core.magic import register_line_magic
from IPython.core.getipython import get_ipython

import traceback

def store_exception(shell, etype, evalue, tb, tb_offset=None):
    # Create a plain text traceback formatter
    styled_exception = shell.showtraceback()

    prompt_number = shell.execution_count
    err = shell.user_ns.get("Err", {})
    err[prompt_number] = styled_exception
    shell.user_ns["Err"] = err
