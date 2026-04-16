"""
The calculate tool evaluates simple arithmetic expressions.
"""


def run_calculate(expression):
    """
    Evaluate a simple arithmetic expression and return the result as text.

    >>> run_calculate("2 + 2")
    '4'
    >>> run_calculate("10 - 3")
    '7'
    >>> "Error:" in run_calculate("hello")
    True
    """
    try:
        allowed_globals = {"__builtins__": {}}
        result = eval(expression, allowed_globals, {})
        return str(result)
    except Exception as e:
        return f"Error: {e}"
