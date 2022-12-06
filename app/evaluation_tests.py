import unittest

try:
    from .evaluation import evaluation_function, parse_error_warning
except ImportError:
    from evaluation import evaluation_function, parse_error_warning


class TestEvaluationFunction(unittest.TestCase):
    """
    TestCase Class used to test the algorithm.
    ---
    Tests are used here to check that the algorithm written
    is working as it should.

    It's best practise to write these tests first to get a
    kind of 'specification' for how your algorithm should
    work, and you should run these tests before committing
    your code to AWS.

    Read the docs on how to use unittest here:
    https://docs.python.org/3/library/unittest.html

    Use evaluation_function() to check your algorithm works
    as it should.
    """

    def assertEqual_input_variations(self, response, answer, params, value):
        result = evaluation_function(response, answer, params)
        self.assertEqual(result.get("is_correct"), value)
        variation_definitions = [lambda x : x.replace('**','^'),
                                 lambda x : x.replace('**','^').replace('*',' '),
                                 lambda x : x.replace('**','^').replace('*','')]
        for variation in variation_definitions:
            response_variation = variation(response)
            answer_variation = variation(answer)
            if (response_variation != response) or (answer_variation != answer):
                result = evaluation_function(response_variation, answer, params)
                self.assertEqual(result.get("is_correct"), value)
                result = evaluation_function(response, answer_variation, params)
                self.assertEqual(result.get("is_correct"), value)
                result = evaluation_function(response_variation, answer_variation , params)
                self.assertEqual(result.get("is_correct"), value)

    def test_simple_polynomial_correct(self):
        response = "3*x**2 + 3*x +  5"
        answer = "2+3+x+2*x + x*x*3"
        params = {"strict_syntax": False}

        self.assertEqual_input_variations(response, answer, params, True)

    def test_simple_polynomial_with_input_symbols_correct(self):
        response = "3*longName**2 + 3*longName + 5"
        answer = "2+3+longName+2*longName + 3*longName * longName"
        params = {"strict_syntax": False, "input_symbols": [["longName",[]]]}

        self.assertEqual_input_variations(response, answer, params, True)

    def test_simple_polynomial_with_input_symbols_implicit_correct(self):
        response = "abcxyz"
        answer = "abc*xyz"
        params = {"strict_syntax": False, "input_symbols": [["abc",[]],["xyz",[]]]}
        result = evaluation_function(response, answer, params)
        self.assertEqual(result["is_correct"],True)

    def test_simple_polynomial_incorrect(self):
        response = "3*x**2 + 3*x +  5"
        answer = "2+3+x+2*x + x*x*3 - x"
        params = {"strict_syntax": False}

        self.assertEqual_input_variations(response, answer, params, False)

    def test_simple_trig_correct(self):
        response = "cos(x)**2 + sin(x)**2 + y"
        answer = "y + 1"
        params = {"strict_syntax": False}

        self.assertEqual_input_variations(response, answer, params, True)

    def test_complicated_expression_correct(self):
        params = {"strict_syntax": False, "symbol_assumptions": "('x','positive')"}
        response = "1/( ((x+1)**2) * ( sqrt(1-(x/(x+1))**2) ) )"
        answer = "1/((x+1)*(sqrt(2x+1)))"
        self.assertEqual_input_variations(response, answer, params, True)
        response = "1/((x+1)*(sqrt(2x+1)))"
        answer = "1/( ((x+1)**2) * ( sqrt(1-(x/(x+1))**2) ) )"
        self.assertEqual_input_variations(response, answer, params, True)

    def test_simple_fractional_powers_correct(self):
        params = {"strict_syntax": False, "symbol_assumptions": "('g','positive') ('v','positive')"}
        fractional_powers_res = ["sqrt(v)/sqrt(g)","v**(1/2)/g**(1/2)","v**(0.5)/g**(0.5)"]
        fractional_powers_ans = ["sqrt(v/g)","(v/g)**(1/2)","(v/g)**(0.5)"]
        for response in fractional_powers_ans:
            for answer in fractional_powers_ans:
                self.assertEqual_input_variations(response, answer, params, True)
        fractional_powers_res = ["v**(1/5)/g**(1/5)","v**(0.2)/g**(0.2)"]
        fractional_powers_ans = ["(v/g)**(1/5)","(v/g)**(0.2)"]
        for response in fractional_powers_ans:
            for answer in fractional_powers_ans:
                self.assertEqual_input_variations(response, answer, params, True)
        response = "v**(1/n)/g**(1/n)"
        answer = "(v/g)**(1/n)"
        self.assertEqual_input_variations(response, answer, params, True)

    def test_invalid_user_expression(self):
        response = "a*(b+c"
        answer = "a*(b+c)"
        result = evaluation_function(response,answer,{})
        self.assertEqual(parse_error_warning(response) in result["feedback"], True)

    def test_invalid_author_expression(self):
        body = {"response": "3*x", "answer": "3x"}

        self.assertRaises(
            Exception,
            evaluation_function,
            body["response"],
            body["answer"],
            {},
        )

    def test_recp_trig_correct(self):
        response = "1+tan(x)**2 + y"
        answer = "sec(x)**2 + y"
        params = {"strict_syntax": False}

        self.assertEqual_input_variations(response, answer, params, True)

    def test_decimals_correct(self):
        response = "x/2"
        answer = "0.5*x"
        params = {"strict_syntax": False}

        self.assertEqual_input_variations(response, answer, params, True)

    def test_absolute_correct(self):
        response = "|x|+y"
        answer = "Abs(x)+y"
        params = {"strict_syntax": False}

        self.assertEqual_input_variations(response, answer, params, True)

    def test_absolute_ambiguity(self):
        response = "a|x|+|y|"
        answer = "a*Abs(x)+Abs(y)"
        params = {"strict_syntax": False}

        result = evaluation_function(response, answer, params)
        self.assertEqual(result["is_correct"], True)
        self.assertEqual("Notation in response might be ambiguous, use Abs(.) instead of |.|" in result["feedback"], True)

        response = "|x|a+|y|"
        answer = "a*Abs(x)+Abs(y)"
        params = {"strict_syntax": False}

        result = evaluation_function(response, answer, params)
        self.assertEqual(result["is_correct"], True)
        self.assertEqual("Notation in response might be ambiguous, use Abs(.) instead of |.|" in result["feedback"], True)

    def test_nested_absolute_response(self):
        response = "|x+|y||"
        answer = "Abs(x+Abs(y))"
        result = evaluation_function(response, answer, {})
        self.assertEqual(result["is_correct"], True)

        response = "a*|x+b*|y||"
        answer = "a*Abs(x+b*Abs(y))"
        result = evaluation_function(response, answer, {})
        self.assertEqual(result["is_correct"], True)

    def test_many_absolute_response(self):
        body = {"response": "|x|+|y|", "answer": "Abs(x)+Abs(y)"}

        result = evaluation_function(body["response"], body["answer"], {})

        self.assertEqual(result["is_correct"], True)

    def test_many_absolute_answer(self):
        body = {"response": "|x|+|y|", "answer": "|x|+|y|"}

        result = evaluation_function(body["response"], body["answer"], {})

        self.assertEqual(result["is_correct"], True)

    def test_nested_absolute_answer(self):
        response = "|x+|y||"
        answer = "|x+|y||"
        result = evaluation_function(response, answer, {})
        self.assertEqual(result["is_correct"], True)

        response = "a*|x+b*|y||"
        answer = "a*|x+b*|y||"
        result = evaluation_function(response, answer, {})
        self.assertEqual(result["is_correct"], True)

    def test_absolute_ambiguity_response(self):
        body = {"response": "|a+b|c+d|e+f|", "answer": "|a+b|*c+d*|e+f|"}

        result = evaluation_function(body["response"], body["answer"], {})

        self.assertEqual("Notation in response might be ambiguous, use Abs(.) instead of |.|" in result["feedback"], True)

    def test_absolute_ambiguity_answer(self):
        body = {"response": "|a+b|*c+d*|e+f|", "answer": "|a+b|c+d|e+f|"}

        with self.assertRaises(Exception) as cm:
            evaluation_function(body["response"], body["answer"], {})

        self.assertEqual(cm.exception.args[1] == "ambiguityWith|", True)

    def test_clashing_symbols(self):
        params = {}
        response = "beta+gamma+zeta+I+N+O+Q+S+E"
        answer = "E+S+Q+O+N+I+zeta+gamma+beta"
        result = evaluation_function(response, answer, params)
        self.assertEqual(result.get("is_correct"), True)

    def test_special_constants(self):
        response = "pi"
        answer = "2*asin(1)"
        params = {"strict_syntax": False}

        self.assertEqual_input_variations(response, answer, params, True)

    def test_complex_numbers(self):
        response = "I"
        answer = "(-1)**(1/2)"
        params = {"complexNumbers": True, "strict_syntax": False}

        self.assertEqual_input_variations(response, answer, params, True)

    def test_special_functions(self):
        params = {"specialFunctions": True, "strict_syntax": False}
        response = "beta(1,x)"
        answer = "1/x"
        self.assertEqual_input_variations(response, answer, params, True)
        response = "gamma(5)"
        answer = "24"
        self.assertEqual_input_variations(response, answer, params, True)
        response = "zeta(2)"
        answer = "pi**2/6"
        self.assertEqual_input_variations(response, answer, params, True)

    def test_plus_minus_all_correct(self):
        response = "-minus_plus x**2 - plus_minus y**2"
        answer = "plus_minus x**2 + minus_plus y**2"
        params = {"strict_syntax": False}

        self.assertEqual_input_variations(response, answer, params, True)

    def test_plus_minus_replace_symbols_all_correct(self):
        response = "- -+ x**2 - +- y**2"
        answer = "+- x**2 + -+ y**2"
        params = {"plus_minus": "+-", "minus_plus": "-+", "strict_syntax": False}

        self.assertEqual_input_variations(response, answer, params, True)

    def test_plus_minus_all_incorrect(self):
        response = "plus_minus x**2 - minus_plus y**2"
        answer = "plus_minus x**2 + minus_plus y**2"
        params = {"strict_syntax": False}

        self.assertEqual_input_variations(response, answer, params, False)

    def test_plus_minus_all_responses_correct(self):
        response = "x**2 - y**2"
        answer = "plus_minus x**2 + minus_plus y**2"
        params = {"multiple_answers_criteria": "all_responses", "strict_syntax": False}

        self.assertEqual_input_variations(response, answer, params, True)

    def test_plus_minus_all_responses_incorrect(self):
        response = "-x**2 - y**2"
        answer = "plus_minus x**2 + minus_plus y**2"
        params = {"multiple_answers_criteria": "all_responses", "strict_syntax": False}

        self.assertEqual_input_variations(response, answer, params, False)

    def test_plus_minus_all_answers_correct(self):
        response = "-x**2"
        answer = "plus_minus minus_plus x**2"
        params = {"multiple_answers_criteria": "all_responses", "strict_syntax": False}

        self.assertEqual_input_variations(response, answer, params, True)

    def test_plus_minus_all_answers_incorrect(self):
        response = "x**2"
        answer = "plus_minus minus_plus x**2"
        params = {"multiple_answers_criteria": "all_responses", "strict_syntax": False}

        self.assertEqual_input_variations(response, answer, params, False)

    def test_simplified_in_correct_response(self):
        response = "a*x + b"
        answer = "b + a*x"

        res = evaluation_function(response, answer, {})
        self.assertIn("response_simplified", res)

    def test_simplified_in_wrong_response(self):
        response = "a*x + b"
        answer = "b + a*x + 8"

        res = evaluation_function(response, answer, {})
        self.assertIn("response_simplified", res)

    def test_equality_sign_in_answer_and_response_correct(self):
        response = "2*x**2 = 10*y**2+14"
        answer = "x**2-5*y**2-7=0"
        params = {"strict_syntax": False}

        self.assertEqual_input_variations(response, answer, params, True)

    def test_equality_sign_in_answer_and_response_incorrect(self):
        response = "2*x**2 = 10*y**2+20"
        answer = "x**2-5*y**2-7=0"
        params = {"strict_syntax": False}

        self.assertEqual_input_variations(response, answer, params, False)

    def test_equality_sign_in_answer_not_response(self):
        response = "2*x**2-10*y**2-14"
        answer = "x**2-5*y**2-7=0"
        params = {"strict_syntax": False}

        result = evaluation_function(response, answer, params)
        self.assertEqual(result["is_correct"], False)
        self.assertEqual(result["feedback"], "The response was an expression but was expected to be an equality.")

    def test_equality_sign_in_response_not_answer(self):
        response = "2*x**2 = 10*y**2+14"
        answer = "x**2-5*y**2-7"
        params = {"strict_syntax": False}

        result = evaluation_function(response, answer, params)
        self.assertEqual(result["is_correct"], False)
        self.assertEqual(result["feedback"], "The response was an equality but was expected to be an expression.")

    def test_empty_input_symbols_codes_and_alternatives(self):
        answer = '(1+(gamma-1)/2)((-1)/(gamma-1))'
        response = '(1+(gamma-1)/2)((-1)/(gamma-1))'
        params = {'strict_syntax': False,
                   'input_symbols': [['gamma', ['']], ['', ['A']], [' ', ['B']], ['C', ['  ']]]
                 }
        result = evaluation_function(response, answer, params)
        self.assertEqual(result["is_correct"], True)

    def test_numerical_comparison(self):
        params = {"numerical": True}
        with self.subTest(tag="Correct response, tolerance specified with atol"):
            response = "6.73"
            answer = "sqrt(3)+5"
            params.update({"atol": 0.005})
            result = evaluation_function(response, answer, params)
            self.assertEqual(result["is_correct"], True)

        with self.subTest(tag="Incorrect response, tolerance specified with atol"):
            response = "6.7"
            answer = "sqrt(3)+5"
            params.update({"atol": 0.005})
            result = evaluation_function(response, answer, params)
            self.assertEqual(result["is_correct"], False)

        with self.subTest(tag="Correct response, tolerance specified with rtol"):
            response = "6.73"
            answer = "sqrt(3)+5"
            params.update({"rtol": 0.0005})
            result = evaluation_function(response, answer, params)
            self.assertEqual(result["is_correct"], True)

        with self.subTest(tag="Incorrect response, tolerance specified with rtol"):
            response = "6.7"
            answer = "sqrt(3)+5"
            params.update({"rtol": 0.0005})
            result = evaluation_function(response, answer, params)
            self.assertEqual(result["is_correct"], False)

        with self.subTest(tag="Response is not constant"):
            response = "1.7+x"
            answer = "sqrt(3)+5"
            params.update({"atol": 0.005})
            result = evaluation_function(response, answer, params)
            self.assertEqual(result["is_correct"], False)

        with self.subTest(tag="Answer is not constant, tolerance specified with atol"):
            response = "6.73"
            answer = "sqrt(3)+x"
            params.update({"atol": 0.005})
            result = evaluation_function(response, answer, params)
            self.assertEqual(result["is_correct"], False)

        with self.subTest(tag="Response is not constant, tolerance specified with rtol"):
            response = "6.7+x"
            answer = "sqrt(3)+5"
            params.update({"rtol": 0.0005})
            result = evaluation_function(response, answer, params)
            self.assertEqual(result["is_correct"], False)

        with self.subTest(tag="Answer is not constant, tolerance specified with rtol"):
            response = "6.73"
            answer = "sqrt(3)+x"
            params.update({"rtol": 0.0005})
            result = evaluation_function(response, answer, params)
            self.assertEqual(result["is_correct"], False)

    def test_warning_inappropriate_symbol(self):
        answer = '2**4'
        response = '2^4'
        params = {'strict_syntax': True }
        result = evaluation_function(response, answer, params)
        self.assertEqual(result["feedback"], "Note that `^` cannot be used to denote exponentiation, use `**` instead.")

        answer = '2**4'
        response = '2^0.5'
        params = {'strict_syntax': True }
        result = evaluation_function(response, answer, params)
        self.assertEqual(result["feedback"], parse_error_warning(response)+"\n"+"Note that `^` cannot be used to denote exponentiation, use `**` instead.")

    def test_error_inappropriate_symbol(self):
        answer = '0.5'
        response = '0,5'
        params = {'strict_syntax': True }
        result = evaluation_function(response, answer, params)
        self.assertEqual(parse_error_warning(response) in result["feedback"], True)

        answer = '(0.002*6800*v)/1.2'
        response = '(0,002*6800*v)/1,2'
        params = {'strict_syntax': False }
        result = evaluation_function(response, answer, params)
        self.assertEqual(parse_error_warning(response) in result["feedback"], True)

        answer = '-inf'
        response = '-∞'
        params = {'strict_syntax': False }
        result = evaluation_function(response, answer, params)
        self.assertEqual(parse_error_warning(response) in result["feedback"], True)

        answer = 'x*y'
        response = 'x.y'
        params = {'strict_syntax': False }
        result = evaluation_function(response, answer, params)
        self.assertEqual(parse_error_warning(response) in result["feedback"], True)

    def test_empty_response_answer(self):
        with self.subTest(tag="Empty response"):
            answer = "5*x"
            response = ""
            result = evaluation_function(response, answer, {})
            self.assertEqual(result["feedback"], "No response submitted.")
        with self.subTest(tag="Whitespace response"):
            answer = "5*x"
            response = "  \t\n"
            result = evaluation_function(response, answer, {})
            self.assertEqual(result["feedback"], "No response submitted.")
        with self.subTest(tag="Whitespace answer"):
            answer = ""
            response = "5*x"
            self.assertRaises(
                Exception,
                evaluation_function,
                response,
                answer,
                {},
            )
        with self.subTest(tag="Whitespace answer"):
            answer = "  \t\n"
            response = "5*x"
            self.assertRaises(
                Exception,
                evaluation_function,
                response,
                answer,
                {},
            )

    def test_AAA_slow_response(self):
        params = {"strict_syntax": False,
                  "input_symbols": [["fx",["f","f_x","fofx"]],\
                                    ["C",["c","k","K"]],\
                                    ["A",["a"]],\
                                    ["B",["b"]],\
                                    ["x",["X"]],\
                                    ["y",["Y"]]]}
        with self.subTest(tag="With `fx` in response"):
            answer = "-A*exp(x/b)*sin(y/b)+fx+C"
            response = "-A*exp(x/b)*sin(y/b)+fx+C"
            result = evaluation_function(response, answer, params)
            self.assertEqual(result["is_correct"], True)

        with self.subTest(tag="With `e^` in response"):
            answer = "-A*e^(x/b)*sin(y/b)+fx+C"
            response = "-A*e^(x/b)*sin(y/b)+fx+C"
            result = evaluation_function(response, answer, params)
            self.assertEqual(result["is_correct"], True)

        with self.subTest(tag="Without `-` in response"):
            answer = "A*exp(x/b)*sin(y/b)+fx+C"
            response = "A*exp(x/b)*sin(y/b)+fx+C"
            result = evaluation_function(response, answer, params)
            self.assertEqual(result["is_correct"], True)

        with self.subTest(tag="With `f(x)` in response"):
            answer = "A*exp(x/b)*sin(y/b)+f(x)+C"
            response = "-A*exp(x/b)*sin(y/b)+f(x)+C"
            result = evaluation_function(response, answer, params)
            self.assertEqual(result["is_correct"], False)

    def test_pi_with_rtol(self):
        answer = "pi"
        response = "3.14"
        params = {"strict_syntax": False,
                  "rtol": 0.05,
                  "input_symbols": [["pi",["Pi","PI","π"]]]}
        result = evaluation_function(response, answer, params)
        self.assertEqual(result["is_correct"], True)

    def test_PHYS40002(self):
        with self.subTest(tag="2.2 b)"):
            params = {"strict_syntax": False}
            answer = "-(y*sin(x*y) + e^(y)) / (x*(e^(y) + sin(x*y)))"
            responses = [
                "-(ysin(x*y) + exp(y)) / (x*(exp(y) + sin(x*y)))",
                "-(sin(xy)y+(e^y))/(x(e^y+sin(xy)x))",
                "sin(xy)y",
                "sin(xy)x",
                "x(e^y+sin(xy)x)",
                "e^y+sin(xy)x"
                ]
            for response in responses:
                result = evaluation_function(response, answer, params)
                self.assertEqual(result["is_correct"], False)

        with self.subTest(tag="2.6 a)"):
            params = {"strict_syntax": False}
            answer = "6*cos(5*x+1)-90*x*sin(5*x+1)-225*x**2*cos(5*x+1)+125*x**3*sin(5*x+1)"
            response = "-90xsin(5x+1)"
            result = evaluation_function(response, answer, params)
            self.assertEqual(result["is_correct"], False)
            responses = [
                "6cos(5x+1)-90x*sin(5x+1)-225x^2cos(5x+1)+125x^3sin(5x+1)"
                "6cos(5x+1)-90xsin(5x+1)-225x^2cos(5x+1)+125x^3sin(5x+1)",
                "(125x^3)*(cos(5x+1))-(225x^2)*(cos(5x+1))-(90x)*(sin(5x+1))+6cos(5x+1)",
                ]
            for response in responses:
                result = evaluation_function(response, answer, params)
                self.assertEqual(result["is_correct"], False)

    def test_latex_expression(self):
        params = {"strict_syntax": False}
        with self.subTest(tag="frac"):
            answer = "(x+1)/(x+2)"
            response = {"response": r"\frac{x+1}{x+2}", "is_latex" : True}
            result = evaluation_function(response, answer, params)
            self.assertEqual(result["is_correct"], True)
        with self.subTest(tag="exp"):
            answer = "x^3"
            response = {"response": r"x^{3}", "is_latex" : True}
            result = evaluation_function(response, answer, params)
            self.assertEqual(result["is_correct"], True)
        with self.subTest(tag="derivative"):
            answer = "t"
            response = {"response": r"\frac{d}{dx} tx", "is_latex" : True}
            result = evaluation_function(response, answer, params)
            self.assertEqual(result["is_correct"], True)
        with self.subTest(tag="sin"):
            answer = "sin(x*pi)"
            response = {"response": r"\sin{x\pi}", "is_latex" : True}
            result = evaluation_function(response, answer, params)
            self.assertEqual(result["is_correct"], True)
        with self.subTest(tag="log"):
            answer = "log(x, 10)"
            response = {"response": r"\log_{10} x", "is_latex" : True}
            result = evaluation_function(response, answer, params)
            self.assertEqual(result["is_correct"], True)
        with self.subTest(tag="logexp"):
            answer = "10G"
            response = {"response": r"10*e^{\ln{G}}", "is_latex" : True}
            result = evaluation_function(response, answer, params)
            self.assertEqual(result["is_correct"], True)

if __name__ == "__main__":
    unittest.main()
