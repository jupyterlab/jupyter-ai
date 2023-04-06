from IPython.core.magic import register_line_magic

import traceback

def store_exception(shell, etype, evalue, tb, tb_offset=None):
    prompt_number = shell.execution_count
    err = shell.user_ns.get("Err", {})
    err[prompt_number] = str(etype) + str(evalue) + str(traceback.format_tb(tb))
    shell.user_ns["Err"] = err
    # Rereaise the exception
    raise
