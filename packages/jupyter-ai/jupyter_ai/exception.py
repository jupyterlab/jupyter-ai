from IPython.core import ultratb
from IPython.core.magic import register_line_magic
from IPython.core.getipython import get_ipython

import traceback

def store_exception(shell, etype, evalue, tb, tb_offset=None):
    # Create a plain text traceback formatter
    tb_formatter = ultratb.FormattedTB(color_scheme='NoColor')
    tb_formatter.set_mode('Verbose')
    styled_exception = '\n'.join(tb_formatter.structured_traceback(etype, evalue, tb, tb_offset))

    prompt_number = shell.execution_count
    err = shell.user_ns.get("Err", {})
    err[prompt_number] = styled_exception
    shell.user_ns["Err"] = err
    # Rereaise the exception
    raise
