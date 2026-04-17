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
        # what you had was pretty dangerous and I'm 
        # not sure where you got it from since it
        # doesn't match what we did in class or 
        # the tutorial code
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"Error: {e}"
