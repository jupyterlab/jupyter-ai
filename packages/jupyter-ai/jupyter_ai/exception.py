from IPython.core.magic import register_line_magic

def store_exception(shell, etype, evalue, tb, tb_offset=None):
    prompt_number = shell.execution_count
    err = shell.user_ns.get("Err", {})
    err[prompt_number] = str(evalue)
    shell.user_ns["Err"] = err
