from typing import Dict, TypedDict

import sympy
from latex2sympy2 import latex2sympy
from sympy.parsing import parse_expr
from sympy.printing.latex import LatexPrinter
from typing_extensions import NotRequired

SymbolDict = Dict[str, str]


class Response(TypedDict):
    response: str
    is_latex: bool


class Params(TypedDict):
    simplify: NotRequired[bool]
    symbols: NotRequired[SymbolDict]


class Preview(TypedDict):
    latex: str
    sympy: str


class Result(TypedDict):
    preview: Preview


def sympy_symbols(symbols: SymbolDict) -> Dict[str, sympy.Symbol]:
    """Create a mapping of local variables for parsing sympy expressions.

    Args:
        symbols (SymbolDict): A dictionary of sympy symbol strings to LaTeX
        symbol strings.

    Note:
        Note, only the sympy string is used in this function.

    Returns:
        Dict[str, sympy.Symbol]: A dictionary of sympy symbol strings to sympy
        Symbol objects.
    """
    return {k: sympy.Symbol(k) for k in symbols}


def latex_symbols(symbols: SymbolDict) -> Dict[sympy.Symbol, str]:
    """Create a mapping between custom Symbol objects and LaTeX symbol strings.
    Used when parsing a sympy Expression to a LaTeX string.

    Args:
        symbols (SymbolDict): A dictionary of sympy symbol strings to LaTeX
        symbol strings.

    Returns:
        Dict[sympy.Symbol, str]: A dictionary of sympy Symbol objects to LaTeX
        strings.
    """
    return {sympy.Symbol(k): v for (k, v) in symbols.items()}


def parse_latex(response: str, symbols: SymbolDict) -> str:
    """Parse a LaTeX string to a sympy string while preserving custom symbols.

    Args:
        response (str): The LaTeX expression to parse.
        symbols (SymbolDict): A mapping of sympy symbol strings and LaTeX
        symbol strings.

    Raises:
        ValueError: If the LaTeX string or symbol couldn't be parsed.

    Returns:
        str: The expression in sympy syntax.
    """
    substitutions = {}

    for sympy_symbol_str, latex_symbol_str in symbols.items():
        try:
            latex_symbol = latex2sympy(latex_symbol_str)
        except Exception:
            raise ValueError(
                f"Couldn't parse latex symbol {latex_symbol_str} "
                f"to sympy symbol."
            )

        substitutions[latex_symbol] = sympy.Symbol(sympy_symbol_str)

    try:
        expression = latex2sympy(response, substitutions)

        if isinstance(expression, list):
            expression = expression.pop()

        return str(expression.xreplace(substitutions))  # type: ignore

    except Exception as e:
        raise ValueError(str(e))


def preview_function(response: Response, params: Params) -> Result:
    """
    Function used to preview a student response.
    ---
    The handler function passes three arguments to preview_function():

    - `response` which are the answers provided by the student.
    - `params` which are any extra parameters that may be useful,
        e.g., error tolerances.

    The output of this function is what is returned as the API response
    and therefore must be JSON-encodable. It must also conform to the
    response schema.

    Any standard python library may be used, as well as any package
    available on pip (provided it is added to requirements.txt).

    The way you wish to structure you code (all in this function, or
    split into many) is entirely up to you.
    """
    symbols: SymbolDict = params.get("symbols", {})

    if "is_latex" not in response:
        raise ValueError("`is_latex` wasn't passed in response.")
    elif "response" not in response:
        raise ValueError("`response` wasn't passed in response.")

    if not response["response"]:
        return Result(preview=Preview(latex="", sympy=""))

    try:
        if response["is_latex"]:
            response["response"] = parse_latex(response["response"], symbols)

        equation = parse_expr(
            response["response"],
            evaluate=False,
            local_dict=sympy_symbols(symbols),
            transformations="all",
        )

        if params.get("simplify", False):
            equation = sympy.simplify(equation)

        latex_out = LatexPrinter(
            {"symbol_names": latex_symbols(symbols)}
        ).doprint(equation)

        sympy_out = str(equation)

    except SyntaxError as e:
        raise ValueError("Failed to parse Sympy expression") from e
    except ValueError as e:
        raise ValueError("Failed to parse LaTeX expression") from e

    return Result(preview=Preview(latex=latex_out, sympy=sympy_out))
