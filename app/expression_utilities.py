# -------- String Manipulation Utilities
def preprocess_expression(exprs, params):
    """
    Input:
        exprs  : a string or a list of strings
        params : Evaluation function parameter dictionary
    Output:
        List of strings where alternatives for input symbols have been replaced with
        their corresponsing input symbol code.
    Remark:
        Alternatives are sorted before substitution so that longer alternatives takes precedence.
    """
    if isinstance(exprs, str):
        exprs = [exprs]

    if "symbols" in params.keys():
        input_symbols = params["symbols"]
        input_symbols_to_remove = []
        alternatives_to_remove = []
        for k in range(0, len(input_symbols)):
            if len(input_symbols[k]) > 0:
                input_symbols[k][0].strip()
                if len(input_symbols[k][0]) == 0:
                    input_symbols_to_remove += [k]
            else:
                for i in range(0, len(input_symbols[k][1])):
                    if len(input_symbols[k][1][i]) > 0:
                        input_symbols[k][1][i].strip()
                    if len(input_symbols[k][1][i]) == 0:
                        alternatives_to_remove += [(k, i)]
        for k, i in alternatives_to_remove:
            del input_symbols[k][1][i]
        for k in input_symbols_to_remove:
            del input_symbols[k]
        substitutions = []
        for input_symbol in params["symbols"]:
            substitutions.append((input_symbol[0], input_symbol[0]))
            for alternative in input_symbol[1]:
                if len(alternative) > 0:
                    substitutions.append((alternative, input_symbol[0]))
        substitutions.sort(key=lambda x: -len(x[0]))

        for k in range(0, len(exprs)):
            exprs[k] = substitute(exprs[k], substitutions)

    return exprs


def substitute(string, substitutions):
    """
    Input:
        string        : a string or a list of strings
        substitutions : a list of pairs of strings
    Output:
        A string that is the input string where any occurence of the left element
        of each pair in substitutions have been replaced with the corresponding right element.
    Remarks:
        Substitutions are made in the input order but if a substitutions left element is a
        substring of a preceding substitutions right element there will be no substitution.
        In most cases it is good practice to sort the substitutions by the length of the left
        element in descending order.
        Examples:
            substitute("abc bc c", [("abc","p"), ("bc","q"), ("c","r")])
            returns: "p q r"
            substitute("abc bc c", [("c","r"), ("bc","q"), ("abc","p")])
            returns: "abr br r"
            substitute("p bc c", [("p","abc"), ("bc","q"), ("c","r")])
            returns: "abc q c"
            substitute("p bc c", [("c","r"), ("bc","q"), ("p","abc")])
            returns: "abc br r"
    """
    if isinstance(string, str):
        string = [string]

    # Perform substitutions
    new_string = []
    for part in string:
        if not isinstance(part, str):
            new_string.append(part)
        else:
            index = 0
            string_buffer = ""
            while index < len(part):
                matched_start = False
                for k, pair in enumerate(substitutions):
                    if part.startswith(pair[0], index):
                        matched_start = True
                        if len(string_buffer) > 0:
                            new_string.append(string_buffer)
                            string_buffer = ""
                        new_string.append(k)
                        index += len(pair[0])
                        break
                if not matched_start:
                    string_buffer += part[index]
                    index += 1
            if len(string_buffer) > 0:
                new_string.append(string_buffer)

    for k, elem in enumerate(new_string):
        if isinstance(elem, int):
            new_string[k] = substitutions[elem][1]

    return "".join(new_string)


# -------- (Sympy) Expression Parsing Utilities

from sympy import Symbol
from sympy.parsing.sympy_parser import T as parser_transformations
from sympy.parsing.sympy_parser import parse_expr, split_symbols_custom


def create_sympy_parsing_params(params, unsplittable_symbols=tuple()):
    """
    Input:
        params               : evaluation function parameter dictionary
        unsplittable_symbols : list of strings that will not be split when parsing
                               even if implicit multiplication is used.
    Output:
        parsing_params: A dictionary that contains necessary info for the
                        parse_expression function.
    """

    if "symbols" in params.keys():
        # unsplittable_symbols += tuple(x[0] for x in params["symbols"])
        to_keep = []
        for symbol in [x[0] for x in params["symbols"]]:
            if len(symbol) > 1:
                to_keep.append(symbol)
        unsplittable_symbols += tuple(to_keep)

    if params.get("specialFunctions", False) == True:
        from sympy import beta, gamma, zeta
    else:
        beta = Symbol("beta")
        gamma = Symbol("gamma")
        zeta = Symbol("zeta")
    if params.get("complexNumbers", False) == True:
        from sympy import I
    else:
        I = Symbol("I")
    E = Symbol("E")
    N = Symbol("N")
    O = Symbol("O")
    Q = Symbol("Q")
    S = Symbol("S")
    symbol_dict = {
        "beta": beta,
        "gamma": gamma,
        "zeta": zeta,
        "I": I,
        "N": N,
        "O": O,
        "Q": Q,
        "S": S,
        "E": E,
    }

    for symbol in unsplittable_symbols:
        symbol_dict.update({symbol: Symbol(symbol)})

    strict_syntax = params.get("strict_syntax", True)

    parsing_params = {
        "unsplittable_symbols": unsplittable_symbols,
        "strict_syntax": strict_syntax,
        "symbol_dict": symbol_dict,
        "extra_transformations": tuple(),
    }

    return parsing_params


def parse_expression(expr, parsing_params):
    """
    Input:
        expr           : string to be parsed into a sympy expression
        parsing_params : dictionary that contains parsing parameters
    Output:
        sympy expression created by parsing expr configured according
        to the parameters in parsing_params
    """
    strict_syntax = parsing_params.get("strict_syntax", False)
    extra_transformations = parsing_params.get("extra_transformations", ())
    unsplittable_symbols = parsing_params.get("unsplittable_symbols", ())
    symbol_dict = parsing_params.get("symbol_dict", {})
    separate_unsplittable_symbols = [
        (x, x + " ") for x in unsplittable_symbols
    ]
    expr = substitute(expr, separate_unsplittable_symbols)
    if strict_syntax:
        transformations = parser_transformations[0:4] + extra_transformations
    else:
        #        # Remove all single character unsplittable symbols
        #        # to reduce risk of splitting function names
        #        to_keep = []
        #        for symbol in unsplittable_symbols:
        #            if len(symbol) > 1:
        #                to_keep.append(symbol)
        #        unsplittable_symbols = tuple(to_keep)
        #        symbol_dict = {x: symbol_dict[x] for x in to_keep}
        transformations = (
            parser_transformations[0:4, 6]
            + extra_transformations
            + (split_symbols_custom(lambda x: x not in unsplittable_symbols),)
            + parser_transformations[8]
        )
    return parse_expr(
        expr, transformations=transformations, local_dict=symbol_dict
    )
