try:
    from .evaluation import evaluation_function, parse_error_warning
except ImportError:
    from evaluation import evaluation_function, parse_error_warning

n = 10
for k in range(0,n):
    params = {"strict_syntax": False}
    answer = "-(y*sin(x*y) + exp(y)) / (x*(exp(y) + sin(x*y)))"
    responses = [
        "-(ysin(x*y) + exp(y)) / (x*(exp(y) + sin(x*y)))",
        #"-(y*sin(x*y)+e^y)/(x*e^y+x*sin(x*y))",
        #"-(sin(xy)y+(e^y))/(x(e^y+sin(xy)x))"
        ]
    #answer = "6*cos(5*x+1)-90*x*sin(5*x+1)-225*x**2*cos(5*x+1)+125*x**3*sin(5*x+1)"
    #responses = [
    #    #"6cos(5x+1)-90x*sin(5x+1)-225x^2cos(5x+1)+125x^3sin(5x+1)" # Correct answer
    #    "6cos(5x+1)-90xsin(5x+1)-225x^2cos(5x+1)+125x^3sin(5x+1)", # Wrong answer (due to issues with implicit multiplication)
    #    ]
    for response in responses:
        result = evaluation_function(response, answer, params)
        print(result["is_correct"])