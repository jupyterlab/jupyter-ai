from IPython.core.magic import register_line_magic
from IPython.core.ultratb import ListTB


def store_exception(shell, etype, evalue, tb, tb_offset=None):
    # A structured traceback (a list of strings) or None

    if issubclass(etype, SyntaxError):
        # Disable ANSI color strings
        shell.SyntaxTB.color_toggle()
        # Don't display a stacktrace because a syntax error has no stacktrace
        stb = shell.SyntaxTB.structured_traceback(etype, evalue, [])
        stb_text = shell.SyntaxTB.stb2text(stb)
        # Re-enable ANSI color strings
        shell.SyntaxTB.color_toggle()
    else:
        # Disable ANSI color strings
        shell.InteractiveTB.color_toggle()
        stb = shell.InteractiveTB.structured_traceback(
            etype, evalue, tb, tb_offset=tb_offset
        )
        stb_text = shell.InteractiveTB.stb2text(stb)
        # Re-enable ANSI color strings
        shell.InteractiveTB.color_toggle()

    etraceback = shell.showtraceback()

    styled_exception = str(stb_text)

    prompt_number = shell.execution_count
    err = shell.user_ns.get("Err", {})
    err[prompt_number] = styled_exception
    shell.user_ns["Err"] = err

    # Return
    return etraceback
