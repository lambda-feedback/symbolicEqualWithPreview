import unittest

try:
    from .preview import Params, Response, preview_function
except ImportError:
    from preview import Params, Response, preview_function


class TestPreviewFunction(unittest.TestCase):
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

    Use preview_function() to check your algorithm works
    as it should.
    """

    def test_empty_latex_expression(self):
        response = Response(response="", is_latex=True)
        params = Params()
        result = preview_function(response, params)
        self.assertIn("preview", result)

        preview = result["preview"]
        self.assertEqual(preview["latex"], "")

    def test_empty_sympy_expression(self):
        response = Response(response="", is_latex=False)
        params = Params()
        result = preview_function(response, params)
        self.assertIn("preview", result)
        self.assertNotIn("error", result)

        preview = result["preview"]
        self.assertEqual(preview["sympy"], "")

    def test_latex_and_sympy_are_returned(self):
        response = Response(response="x+1", is_latex=True)
        params = Params()
        result = preview_function(response, params)
        self.assertIn("preview", result)
        self.assertNotIn("error", result)

        preview = result["preview"]

        self.assertIn("latex", preview)
        self.assertIn("sympy", preview)

        response = Response(response="x+1", is_latex=False)
        params = Params()
        result = preview_function(response, params)
        self.assertIn("preview", result)
        self.assertNotIn("error", result)

        preview = result["preview"]

        self.assertIn("latex", preview)
        self.assertIn("sympy", preview)

    def test_doesnt_simplify_latex_by_default(self):
        response = Response(response="\\frac{x + x^2 + x}{x}", is_latex=True)
        params = Params()
        result = preview_function(response, params)
        preview = result["preview"]

        self.assertEqual(preview.get("sympy"), "(x**2 + x + x)/x")

    def test_doesnt_simplify_sympy_by_default(self):
        response = Response(response="(x + x**2 + x)/x", is_latex=False)
        params = Params()
        result = preview_function(response, params)
        self.assertNotIn("error", result)
        preview = result["preview"]

        self.assertEqual(preview.get("latex"), "\\frac{x^{2} + x + x}{x}")

    def test_simplifies_latex_on_param(self):
        response = Response(response="\\frac{x + x^2 + x}{x}", is_latex=True)
        params = Params(simplify=True)
        result = preview_function(response, params)
        self.assertNotIn("error", result)
        preview = result["preview"]

        self.assertEqual(preview.get("sympy"), "x + 2")

    def test_simplifies_sympy_on_param(self):
        response = Response(response="(x + x**2 + x)/x", is_latex=False)
        params = Params(simplify=True)
        result = preview_function(response, params)
        self.assertNotIn("error", result)
        preview = result["preview"]

        self.assertEqual(preview.get("latex"), "x + 2")

    def test_sympy_handles_implicit_multiplication(self):
        response = Response(
            response="sin(x) + cos(2x) - 3x**2", is_latex=False
        )
        params = Params()
        result = preview_function(response, params)
        self.assertNotIn("error", result)

        preview = result["preview"]

        self.assertEqual(
            preview.get("latex"),
            "- 3 x^{2} + \\sin{\\left(x \\right)} "
            "+ \\cos{\\left(2 x \\right)}",
        )

    def test_latex_with_equality_symbol(self):
        response = Response(
            response="\\frac{x + x^2 + x}{x} = y", is_latex=True
        )
        params = Params(simplify=False)
        result = preview_function(response, params)
        self.assertNotIn("error", result)

        preview = result["preview"]

        self.assertEqual(preview.get("sympy"), "Eq((x**2 + x + x)/x, y)")

    def test_sympy_with_equality_symbol(self):
        response = Response(response="Eq((x + x**2 + x)/x, 1)", is_latex=False)
        params = Params(simplify=False)
        result = preview_function(response, params)
        self.assertNotIn("error", result)

        preview = result["preview"]

        self.assertEqual(preview.get("latex"), "\\frac{x^{2} + x + x}{x} = 1")

    def test_latex_conversion_preserves_default_symbols(self):
        response = Response(response="\\mu + x + 1", is_latex=True)
        params = Params(simplify=False)
        result = preview_function(response, params)
        self.assertNotIn("error", result)

        preview = result["preview"]

        self.assertEqual(preview.get("sympy"), "mu + x + 1")

    def test_sympy_conversion_preserves_default_symbols(self):
        response = Response(response="mu + x + 1", is_latex=False)
        params = Params(simplify=False)
        result = preview_function(response, params)
        self.assertNotIn("error", result)

        preview = result["preview"]

        self.assertEqual(preview.get("latex"), "\\mu + x + 1")

    def test_latex_conversion_preserves_optional_symbols(self):
        response = Response(
            response="m_{ \\text{table} } + "
            "\\text{hello}_\\text{world} - x + 1",
            is_latex=True,
        )
        params = Params(
            simplify=False,
            symbols={
                "m_table": "m_{\\text{table}}",
                "test": "\\text{hello}_\\text{world}",
            },
        )
        result = preview_function(response, params)
        self.assertNotIn("error", result)

        preview = result["preview"]

        self.assertEqual(preview.get("sympy"), "m_table + test - x + 1")

    def test_sympy_conversion_preserves_optional_symbols(self):
        response = Response(
            response="m_table + test + x + 1",
            is_latex=False,
        )
        params = Params(
            simplify=False,
            symbols={
                "m_table": "m_{\\text{table}}",
                "test": "\\text{hello}_\\text{world}",
            },
        )
        result = preview_function(response, params)
        self.assertNotIn("error", result)

        preview = result["preview"]

        self.assertEqual(
            preview.get("latex"),
            "m_{\\text{table}} + \\text{hello}_\\text{world} + x + 1",
        )

    def test_invalid_latex_returns_error(self):
        response = Response(
            response="\frac{ m_{ \\text{table} } + x + 1 }{x", is_latex=True
        )
        params = Params(
            simplify=False, symbols={"m_table": "m_{\\text{table}}"}
        )

        with self.assertRaises(ValueError):
            preview_function(response, params)

    def test_invalid_sympy_returns_error(self):
        response = Response(response="x + x***2 - 3 / x 4", is_latex=False)
        params = Params(simplify=False)

        with self.assertRaises(ValueError):
            preview_function(response, params)


if __name__ == "__main__":
    unittest.main()
