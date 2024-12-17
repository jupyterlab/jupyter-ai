import types
import inspect

# These globals are provided by ipython
# and are not needed for autocomplete
IPYTHON_GLOBALS = [
    "In",
    "Out",
    "get_ipython",
    "exit",
    "quit",
    "open",
    "Err",
    "filter_globals"
]

def _is_defined_in_main(val):
    """
    When a variable is defined in main, the source file path
    is not available for it and the function throws

    TODO: Find if there is a better way to filter out objects
    that are imported. For example, when we do from datetime import datetime
    we typically do not want to pollute autocomplete with datetime
    """
    try:
        inspect.getsourcefile(val)
        return False
    except:
        return True

def filter_globals(data: dict):
    """
    Utility method to fetch autocompletes that is used by the frontend
    when user triggers it using @ for variable context insertion
    """
    return [
        key
        for key, value in data.items()
        if not key.startswith('_')
        and key not in IPYTHON_GLOBALS
        and _is_defined_in_main(value)
    ]