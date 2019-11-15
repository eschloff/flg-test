import csv
import random
import html
import json
from contextlib import contextmanager
from collections import defaultdict
import sympy as sym
import re
import os
import zlib
import sys
from itertools import islice
from itertools import count
from collections import OrderedDict
from dataclasses import dataclass, asdict
from typing import List, Any
from pathlib import Path
from sympy import Symbol
from sympy.core.function import _coeff_isneg
from sympy.printing.latex import LatexPrinter, print_latex


@dataclass
class Problem:
    """
    Problem class
    """
    question_stem: str
    explanation: str
    concepts: str
    correct_answer: str = None
    json_blob: str = None
    answer_choices: List[str] = None
    correct_answers: List[str] = None
    incorrect_answers: List[str] = None
    number_of_correct: int = 1
    shuffle: bool = True
    sort_answers: bool = False
    correct_answer_index: Any = None

    def __post_init__(self):
        if self.json_blob:
            assert not self.answer_choices, "Cannot have answer_choices and json_blob"
            assert not self.correct_answers, "Cannot have correct_answers and json_blob"
            assert not self.incorrect_answers, "Cannot have incorrect_answers and json_blob"
        else:
            assert ((self.answer_choices and all(self.answer_choices))
                    or (self.correct_answers
                        and all(self.correct_answers)
                        and self.incorrect_answers
                        and all(self.incorrect_answers))), \
                "Must have answer_choices or correct_answers and incorrect_answers if json_blob is not defined"


def unique(func):
    """
    This is a function decorator. Use it when defining your variables to ensure that they are unique and
    satisfy any of the assertions you make.
    """
    seen = []

    def inner(*args, **kwargs):
        tries = 0
        while True:
            tries += 1
            if tries > 1000:
                raise Exception("Tried to get unique arguments too many times and failed.")

            try:
                res = func(*args, **kwargs)
                if res not in seen:
                    seen.append(res)
                    return res
            except AssertionError:
                continue

    return inner


class Template:
    """Template class for creating assessment templates."""

    def __init__(self):
        name = self.__module__
        if name == '__main__':
            filename = sys.modules[self.__module__].__file__
            name = os.path.splitext(os.path.basename(filename))[0]
        self._seed = zlib.crc32(f'{name}:{self.__class__.__name__}'.encode())
        self.__class__._counters = getattr(self.__class__, '_counters', defaultdict(count))

    def __getattribute__(self, name):
        attr = object.__getattribute__(self, name)
        return attr

    def variables(self):
        raise NotImplementedError()

    def template(self):
        raise NotImplementedError()

    def __call__(self):
        return self.template()

    def __iter__(self):
        while True:
            yield self()

    def take(self, num_problems):
        return list(islice(self, num_problems))


class Printer:
    """
    Printer class for printing assessment templates.
    """

    def __init__(self, learning_objective, is_algo=False, is_quiz=False, is_formative=False):

        self.learning_objective = learning_objective
        self._LO_name = self.learning_objective.lower().replace(" ", "_").replace(",", "")
        self._count = count(1)

        if is_algo:
            self._quiz = "_algo"
        elif is_quiz:
            self._quiz = "_quiz"
        elif is_formative:
            self._quiz = "_formative"
        else:
            self._quiz = ""

        output_path = Path('.') / 'output'
        output_path.mkdir(exist_ok=True)

        self.file_path_csv = output_path / '{}{}.csv'.format(self._LO_name, self._quiz)
        self.file_path_html = output_path / '{}{}.html'.format(self._LO_name, self._quiz)

        self.row = OrderedDict([
            ("Module URL", ""),
            ("Start New Sequence?", "Y"),
            ("Start New Atom?", "Y"),
            ("Learning Objective Description", self.learning_objective),
            ("Concepts", ""),
            ("Type", ""),
            ("Title", ""),
            ("Atom Type", "AB"),
            ("Quiz?", "Y" if (is_algo or is_quiz) else ""),
            ("Atom Header", ""),
            ("Atom Body", ""),
            ("Choice A", ""),
            ("Choice B", ""),
            ("Choice C", ""),
            ("Choice D", ""),
            ("Choice E", ""),
            ("Choice F", ""),
            ("Choice G", ""),
            ("Correct Answer", ""),
            ("Learnosity JSON", ""),
            ("General Explanation", ""),
            ("Author", "Knewton"),
            ("Source URL", "http://www.knewton.com"),
            ("License", "CC_BY_NC_ND"),
        ])

        with self.file_path_csv.open('w') as f:
            w = csv.DictWriter(f, self.row.keys(), lineterminator="\n")
            w.writeheader()
        self.start_html_file()

    def print_problems(self, question_stem, explanation, concepts,
                       correct_answer=None, json_blob=None,
                       answer_choices=None, correct_answers=None, incorrect_answers=None,
                       number_of_correct=1, shuffle=True, sort_answers=False, correct_answer_index=None):

        problem_number = next(self._count)

        row = self.row.copy()

        row["Concepts"] = concepts
        row["Type"] = "LEA" if json_blob else "MC"
        row["Title"] = self.learning_objective
        row["Atom Type"] = "AB"
        row["Atom Body"] = question_stem
        row["Learnosity JSON"] = json_blob
        row["General Explanation"] = explanation

        if problem_number > 1 and self._quiz == "_algo":
            row["Start New Sequence?"] = "N"
            row["Start New Atom?"] = "N"

        # Mix the correct and incorrect answers together
        if correct_answers and incorrect_answers:
            answer_choices = list(correct_answers) + list(incorrect_answers)
            number_of_correct = len(list(correct_answers))

        if answer_choices:
            if correct_answer_index is not None:
                if isinstance(correct_answer_index, list):
                    correct_answer = ",".join(["ABCDEFG"[i] for i in correct_answer_index])
                else:
                    correct_answer = "ABCDEFG"[correct_answer_index]
            elif sort_answers:
                def sort_key(x):
                    item = str(x[1]).replace("$_", "")
                    item = int(item) if item.isdigit() else item
                    return item

                c = sorted(list(enumerate(answer_choices)), key=lambda x: sort_key(x))
                print(c)
                answer_indices, answer_choices = zip(*c)
                correct_answer = ",".join(["ABCDEFG"[answer_indices.index(i)] for i in range(number_of_correct)])
            elif shuffle:
                c = list(enumerate(answer_choices))
                random.shuffle(c)
                answer_indices, answer_choices = zip(*c)
                correct_answer = ",".join(["ABCDEFG"[answer_indices.index(i)] for i in range(number_of_correct)])
            else:
                c = list(enumerate(answer_choices))
                answer_indices, answer_choices = zip(*c)
                correct_answer = ",".join(["ABCDEFG"[answer_indices.index(i)] for i in range(number_of_correct)])

            for (choice, letter) in zip(answer_choices, "ABCDEFG"):
                row[f"Choice {letter}"] = choice

        if correct_answer:
            row["Correct Answer"] = correct_answer

        with self.file_path_csv.open('a') as f:
            w = csv.DictWriter(f, row.keys(), lineterminator="\n")
            w.writerow(row)

        self.print_problem_to_html(problem_number, question_stem, explanation, correct_answer,
                                   concepts, json_blob, answer_choices)

    def print(self, problem):
        if isinstance(problem, Problem):
            self.print_problems(**asdict(problem))
        else:
            self.print_problems(**problem)

    def print_all(self, *problem_iterables):
        for problems in problem_iterables:
            if self._quiz == "_algo":
                self._count = count(1)
            if isinstance(problems, tuple) and len(problems) == 2:
                problems, num_problems = problems
                for problem in islice(problems, num_problems):
                    self.print(problem)
            else:
                try:
                    for problem in problems:
                        self.print(problem)
                except TypeError:
                    self.print(problems)
        self.finish_html_file()

    def start_html_file(self):
        """
        Opens new HTML file and begins writing to it. Writes style information, mathjax scripts for
        rendering math, and begins the left-side div that will contain all question summaries.
        """
        with self.file_path_html.open('w') as f:
            f.write("""
            <html>
            <head> 
            <style>
                body {padding: 0;margin: 0;}
                h2 {margin-left: 10px; margin-right:10px;}
                h3 {margin-left: 10px; margin-right:10px;}
                p {margin-left: 10px; margin-right:10px;}
                div2 {display: inline-block; width: 650px; height: 650px; margin-left: 30px}
                table[data-source='cms-table'] {
                  margin: 0 auto;
                  border-spacing: 0;
                }
                table[data-source='cms-table'] th,
                table[data-source='cms-table'] td {
                  border-bottom: 1px solid var(--grey-100);
                  padding: 0.3rem 1.2rem 0.3rem 1.2rem;
                }
                table[data-type='math-table'] th,
                table[data-type='math-table'] td {
                  text-align: center;
                }
                table[data-type='number-table'] th,
                table[data-type='number-table'] td {
                  text-align: right;
                }
                table[data-type='text-table'] th,
                table[data-type='text-table'] td {
                  text-align: left;
                }
                .left-panel {width: 50%;}
                .right-panel {width: 50%;height: 100%;overflow: hidden; position: fixed;}
                .learnosity-iframe {height: 100%;width: 100%;border:10px;background-color:lightgray;}
                .learnosity-content {display:none;}
                .learnosity-form {text-align:center;}
                .learnosity-button {margin-left:auto; margin-right:auto;}
            </style>
            """ + mathjax_scripts + """
            <script src="https://www.desmos.com/api/v1.3/calculator.js?apiKey=dcb31709b452b1cf9dc26972add0fda6"></script>
            </head>
            <body>
            <div class="left-panel", style='display: inline-block; float: left;'>
            """)

    def print_problem_to_html(self, problem_number: int, question_stem: str, explanation: str,
                              correct_answer: str, concepts: str, learnosity_json: any = None,
                              answer_choices: str = None):
        """Prints this question to output HTML file."""

        with self.file_path_html.open('a') as f:
            f.write(f'<h2> Problem {problem_number} </h2> \n')
            f.write(f'<p> <b>Concept(s):</b> {concepts} </p> \n')
            f.write(f'<h3> Question Stem </h3> \n')
            f.write(f'<p> {question_stem} </p> \n')
            if answer_choices:
                f.write('<h3> Answer Choices </h3> \n <ol type="A">')
                for choice in answer_choices:
                    f.write(f'<li>{choice}</li> \n')
                f.write('</ol>')
            f.write(f'<h3> Explanation </h3> \n')
            f.write(f'<p> {explanation} </p> \n')
            f.write(f'<h3> Correct Answer </h3> \n')
            f.write(f'<p> {correct_answer} </p> \n')

            # If learnosity question, provide a button that can be clicked to preview the
            # Learnosity in iframe on right side of page.
            if learnosity_json:
                f.write("""
                <form class="learnosity-form" name="preview-learnosity" action="https://www.knewton.com/content-dev/preview-learnosity" target="learnosity-iframe" method="post">
                    <input class="learnosity-content" 
                           name="learnosityContent"
                           type="text"
                           value='{ "learnosityContent": """ + html.escape(str(learnosity_json)) + """ }' />
                    <input type="submit" class="learnosity-button" value="Preview learnosity" />
                </form>
    """)
            f.write('\n\n')

    def finish_html_file(self):
        """
        Closes the left-side div for viewing question summaries and writes the right-side div
        that contains an iframe for previewing Learnosity. Closes any remaining tags (html and body)
        """
        with self.file_path_html.open('a') as f:
            f.write('</div> \n')
            f.write("""
                <div class='right-panel' style='display: inline-block; float: left;'>
                    <iframe class="learnosity-iframe" name="learnosity-iframe" srcdoc=""></iframe>
                </div> \n
            """)
            f.write('</body></html>')



def non_zero_select(n, m=None):
    """random non zero number between -n and n or n and m (if m is specified)"""
    if n == 0 and not m:
        return 0
    if m:
        if n * m > 0:
            return random.randint(n, m)
        return random.choice(list(range(n, 0)) + list(range(1, m + 1)))
    else:
        return random.choice(list(range(-n, 0)) + list(range(1, n + 1)))


def terms_string(*args, **kwargs):
    """
    returns a string representing the
    list of terms added together with appropriate signs and _without simplifying_ in the given order
    this replaces the need for lots of crazy string formatting, pmsign, etc. to get signs right
    ex: terms_string(5, 3*x, -2, -x**2, -8*x) returns '5 + 3 x - 2 - x^{2} - 8 x'
    note: this will not include 0 terms
    """
    return sym.latex(sym.Add(*args, evaluate=False), order='none', **kwargs)


def constant_sign(x, leading=False):
    """
    Gives the string x with the appropriate sign in front
    Useful for making strings involving adding a bunch of terms together
    leading tells whether the constant is first, so shouldn't have a plus sign in that case
    constant_sign(3) gives "+3"
    constant_sign(3, True) gives "3"
    constant_sign(-3) gives "-3"
    constant_sign(sympify(1) / 2) gives "+ \frac{1}{2}"
    etc.
    """
    if x >= 0 and not leading:
        return " + %s" % sym.latex(x)
    elif x >= 0 and leading:
        return sym.latex(x)
    elif x < 0:
        return sym.latex(x)


def terms_constants(*args):
    """
    Sum of a bunch of constants with appropriate signs, includes zeros
    """
    first_term = constant_sign(args[0], True)
    other_terms = [constant_sign(arg) for arg in args[1:]]
    return first_term + " ".join(other_terms)


def multiply_terms(*args, left_parens=False, use_parens=True, multiplication_sign=" "):
    """
    returns the string with the args wrapped (if use_parens is True)
    separated by multiplication_sign (default is just putting stuff next to each other)
    """
    if use_parens and left_parens:
        wrapped_args = ["\\left ( %s \\right )" % sym.latex(arg) for arg in args]
    elif use_parens:
        wrapped_args = [sym.latex(args[0])] + ["\\left ( %s \\right )" % sym.latex(arg) for arg in args[1:]]
    else:
        wrapped_args = [sym.latex(arg) for arg in args]
    return multiplication_sign.join(wrapped_args)


def substitute_unsimplified(eval_point, poly, x=sym.symbols('x'), include_parentheses=True, order='lex', color=None,
                            **kwargs):
    """
    Gives the string you would achieve by substituting eval_point into poly without simplifying it
    :param eval_point: the value being substituted into poly
    :param poly: a polynomial
    :param x: the symbol being replaced
    :param include_parentheses: whether to put parentheses around the argument being substituted
    :param order: how the terms are ordered, 'lex' is default (which puts things from highest power to lowest)
    other options are 'none' and 'old' but not sure how those work exactly
    :return: a string of latex representing the substitution of eval_point into poly
    """

    # The asterisks are to avoid any issues when the color name shares a letter with the variable
    x_string = "**" + sym.latex(x) + "**"
    string_of_eval = sym.latex(eval_point, **kwargs)
    string_of_eval = string_of_eval.replace(" ", "")
    if color:
        if include_parentheses:
            string_of_eval = '\\color{%s}{\\left(%s\\right)}' % (color, string_of_eval)
        else:
            string_of_eval = '\\color{%s}{%s}' % (color, string_of_eval)
    else:
        if include_parentheses:
            string_of_eval = '\\left(%s\\right)' % string_of_eval
        else:
            string_of_eval = '%s' % string_of_eval

    function_string = sym.latex(poly, order=order, long_frac_ratio=sym.oo, **kwargs).replace(sym.latex(x), x_string)
    return function_string.replace(x_string, string_of_eval)


def substitute_unsimplified_multiple(eval_points, poly, poly_symbols=sym.symbols('x y'),
                                     include_parentheses=True, order='lex', colors=None, **kwargs):
    """
    Similar to above but with multiple values
    :param eval_points:
    :param poly:
    :param poly_symbols:
    :param include_parentheses:
    :param order:
    :param colors: Should be a list containing the colors in the same order as the variables
    :return:
    """

    variable_strings = ["**" + sym.latex(poly_symbol) + "**" for poly_symbol in poly_symbols]
    strings_of_eval = [sym.latex(eval_point, **kwargs) for eval_point in eval_points]
    strings_of_eval = [string_of_eval.replace(" ", "") for string_of_eval in strings_of_eval]
    function_string = ""

    if colors:
        color = {}
        colors = colors
        for s in strings_of_eval:
            color[s] = colors.pop()

        if include_parentheses:
            strings_of_eval = ['\\color{%s}{\\left(%s\\right)}' % (color[string_of_eval], string_of_eval)
                               for string_of_eval in strings_of_eval]
        else:
            strings_of_eval = ['\\color{%s}{%s}' % (color[string_of_eval], string_of_eval) for string_of_eval
                               in strings_of_eval]
    else:
        if include_parentheses:
            strings_of_eval = ['\\left(%s\\right)' % string_of_eval for string_of_eval in strings_of_eval]
        else:
            strings_of_eval = ['%s' % string_of_eval for string_of_eval in strings_of_eval]

    for symbol, starred_symbol in zip(poly_symbols, variable_strings):
        function_string = sym.latex(poly, order=order, long_frac_ratio=sym.oo, **kwargs).replace(symbol, starred_symbol)

    for variable_string, string_of_eval in zip(variable_strings, strings_of_eval):
        function_string = function_string.replace(variable_string, string_of_eval)
    return function_string


def serialize(*clauses, **kwargs):
    """
    Given foo, bar, gar returns "foo, bar, and gar"
    Given foo, bar returns "foo and bar"
    Includes oxford comma

    If you pass final_word as an argument, it will use that for the conjunction at the end
    For example, if conjunction="or" it will use or instead of and

    :param clauses: list of strings
    :return: strings properly comma'd and and-ed
    """
    conjunction = kwargs.get("conjunction", "and")
    if len(clauses) > 2:
        all_but_last = ", ".join(clauses[:-1])
        return "%s, %s %s" % (all_but_last, conjunction, clauses[-1])
    elif len(clauses) == 2:
        return "%s %s %s" % (clauses[0], conjunction, clauses[1])
    elif len(clauses) == 1:
        return clauses[0]
    else:
        return ''


def gcd_helper(m, n):
    """
    computes the greatest common divisor of m and n
    """
    if m < 0 or n < 0:
        return gcd(abs(m), abs(n))
    if n == 0:
        return m
    if m < n:
        return gcd_helper(n, m)
    return gcd_helper(m % n, n)


def gcd(*args):
    """
    :param args: list of numbers
    :return: greatest common divisor (greatest common factor) of the list of numbers
    """
    if len(args) == 1:
        return args[0]
    return gcd_helper(args[0], gcd(*args[1:]))


def lcm(*args):
    """
    :param args: a list of numbers
    :return: the least common multiple of the list of numbers
    """
    if len(args) == 1:
        return abs(args[0])
    lcm_of_others = lcm(*args[1:])
    return abs(args[0] * lcm_of_others // gcd(args[0], lcm_of_others))


def factors(n):
    """Lists the factors of n"""
    if n == 1:
        return [1]
    i = 1
    l = []
    while i < sym.sqrt(n):
        if n % i == 0:
            l.append(i)
            l.append(n // i)
        i = i + 1
    if sym.sqrt(n * 1.0) == int(sym.sqrt(n)):
        l.append(sym.sqrt(n))
    return l


def random_pythagorean_triple(max_hyp=1555):
    """
    Generates a random Pythagorean triple (a, b, c) using Dickson's method
    :param max_hyp: The maximum size of the hypotenuse
    :return: a, b, c where a^2 + b^2 = c^2
    """
    a = b = 0
    c = max_hyp + 1

    while (c > max_hyp):
        r = random.randint(1, 12) * 2
        rr = r * r // 2

        s = random.choice(factors(rr))
        t = rr // s

        a = r + s
        b = r + t
        c = r + s + t

    return a, b, c


def sorted_nicely(l):
    """ Sort alphnumeric list in the 'natural' way [d, 23, 1, 17, 2, x] --> [1, 2, 17, 23, d, x]"""

    def iconvert(text):
        return int(text) if text.isdigit() else text

    def alphanum_key(key):
        return [iconvert(c) for c in re.split('([0-9]+)', key)]

    return sorted(l, key=alphanum_key)


def rreplace(s, old, new, occurrence):
    """
    Reverse replace. Replaces old with new from right to left, occurrence times.
    Example:
    s = '1232425'
    rreplace(s, '2', ' ', 2)
    '123 4 5'
    rreplace(s, '2', ' ', 3)
    '1 3 4 5'
    rreplace(s, '2', ' ', 4)
    '1 3 4 5'
    """
    li = s.rsplit(old, occurrence)
    return new.join(li)


def convert_hundreds(number):
    """Helper function for num_to_words()"""
    number = int(number)

    ones = ["", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven",
            "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"]

    tens = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]

    if number < 20:
        num = ones[number]

    elif number < 100:
        if number % 10 == 0:
            num = tens[(number // 10) % 10] + ones[number % 10]
        else:
            num = tens[(number // 10) % 10] + "-" + ones[number % 10]

    elif number % 100 < 20:
        num = ones[(number // 100)] + " hundred " + ones[number % 100]

    else:
        if number % 10 == 0:
            num = ones[(number // 100)] + " hundred " + tens[(number // 10) % 10]
        else:
            num = ones[(number // 100)] + " hundred " + tens[(number // 10) % 10] + "-" + ones[number % 10]

    return num


def convert(number):
    """Helper function for num_to_words()"""
    num = ""
    powers = ["", " thousand, ", " million, ", " billion, ", " trillion, ", " quadrillion, ", " quintillion, ",
              " sextillion, ", " septillion, ", " octillion, ", " nonillion, ", " decillion, ", " undecillion, ",
              " duodecillion, ", " tredecillion, ", " quattuordecillion, "]

    for i in range(len(number)):
        if number[i] != 0:
            num = convert_hundreds(number[i]) + powers[i] + num

    return num.replace("  ", ' ')


def num_to_words(n):
    """
    Convert a number to words. Useful for alt-text etc.
    :param n: The number.
    :return: The number in words.
    """
    if not str(n).replace("-", "").isdigit():
        return "%s" % n

    number_in_threes = []

    num = ""
    if n == 0:
        return "zero"
    if n < 0:
        num = "negative "
        n = abs(n)
    while n > 0:
        number_in_threes.append(n % 1000)
        n = n // 1000

    num += convert(number_in_threes)

    if num[-1] == " ":
        num = rreplace(num, " ", "", 1)
    if num[-1] == ",":
        num = rreplace(num, ",", "", 1)

    return num


def pmsign(x, leading=False):
    """
    Gives the string x with the appropriate sign in front
    Useful for making strings involving adding a bunch of terms together
    leading tells whether the constant is first, so shouldn't have a plus sign in that case
    constant_sign(3 * x) gives "+3x"
    constant_sign(3 * x ** 2, Leading=True) gives "3x^2"
    constant_sign(-3) gives "-3"
    constant_sign(x / 2) gives "+ \frac{x}{2}"
    etc.
    """
    x = sym.sympify(x)
    if leading:
        if abs(x) == 1:
            return "" if x > 0 else "-"
        else:
            return sym.latex(x)
    if _coeff_isneg(x):
        return "- %s" % (sym.latex(abs(x)) if x != -1 else "")
    else:
        return "+ %s" % (sym.latex(x) if x != 1 else "")


def mono_coeff(monomial, x=sym.symbols('x')):
    """Returns the leading coefficient of a monomial"""
    return sym.sympify(monomial).subs(x, 1)


def mono_sgn(monomial, x=sym.symbols('x')):
    """Returns the sign, of a monomial"""
    if _coeff_isneg(sym.sympify(monomial)):
        return -1
    return 1


def operator_expand_string(op, *args, x=sym.symbols('x'), end_op=None, parens=True,
                           include_zeros=True, pull_out_const=False,
                           pull_out_leading_negative=True,
                           pull_out_zeroth_order_constants=False, **kwargs):
    """
    Use to apply an operator to a sum or difference of terms. For example
    operator_expand_string('\\int ', x ** 2, 3x^{-2}, end_op=' \\, dx')
    will give \\int \\left(x^2 + 3x^{-2} \\right) \\, dx
    """
    end_op = end_op if end_op else ""

    left_paren = "\\left(" if parens else ""
    right_paren = "\\right)" if parens else ""

    if not include_zeros:
        args = list(filter(lambda a: a != 0, args))

    if pull_out_const:
        if pull_out_zeroth_order_constants:
            coeffs = [mono_coeff(a, x) if sym.diff(a) != 0 else a for a in args]
        else:
            coeffs = [mono_coeff(a, x) if sym.diff(a) != 0 else 1 for a in args]

        coeffs = [1 if coeff == 0 else coeff for coeff in coeffs]

        terms = [
            f"{pmsign(coeffs[0], leading=True)}{op}{left_paren}{polytex(sym.sympify(args[0]) / coeffs[0], **kwargs)}"
            f"{right_paren}{end_op}"]

        terms += [f"{pmsign(coeff)}{op}{left_paren}{polytex(sym.sympify(arg) / coeff, **kwargs)}"
                  f"{right_paren}{end_op}" for (arg, coeff) in zip(args[1:], coeffs[1:])]

    else:
        if pull_out_leading_negative:
            terms = [f"{pmsign(mono_sgn(args[0], x), leading=True)}{op}"
                     f"{left_paren}{polytex(args[0] * mono_sgn(args[0], x), **kwargs)}{right_paren}{end_op}"]
        else:
            terms = [f"{op}{left_paren}{polytex(args[0], **kwargs)}{right_paren}{end_op}"]

        terms += [f"{pmsign(mono_sgn(arg, x))}{op}{left_paren}{polytex(arg * mono_sgn(arg, x), **kwargs)}"
                  f"{right_paren}{end_op}" for arg in args[1:]]

    return " ".join(terms)


def operator_expand(op, poly, x=sym.symbols('x'), pull_out_const=False, **kwargs):
    """
    ***Note that this does not work with negative exponents! This has something to do with sympy generators...***
    Use to apply an operator to a sum or difference of polynomials. For example
    operator_expand('\\frac{d}{dx}', x ** 2 + 3x) will give \\frac{d}{dx}(x^2) + \\frac{d}{dx}(3x)

    Use operator_expand_string instead.
    """

    term_list = [t[1] * x ** t[0][0] for t in sym.Poly(poly, x).terms()]

    coeff_list = [mono_coeff(a, x) if sym.diff(a) != 0 else mono_sgn(a) for a in term_list]
    coeff_list = [1 if coeff == 0 else coeff for coeff in coeff_list]

    if pull_out_const:
        expanded = [
            f"{pmsign(coeff_list[0], leading=True)}{op} "
            f"\\left( {sym.latex(term_list[0] / coeff_list[0], **kwargs)} \\right)"]

        expanded += [f"{pmsign(coeff)}{op} \\left( {sym.latex(term / coeff, **kwargs)} \\right)"
                     for (coeff, term) in zip(coeff_list[1:], term_list[1:])]

    else:
        expanded = [f"{op} \\left( {sym.latex(term_list[0], **kwargs)} \\right)" if coeff_list[0] > 0
                    else f"-{op} \\left( {sym.latex(-term_list[0], **kwargs)} \\right)"]

        expanded += [(f"+{op} \\left( {sym.latex(term, **kwargs)} \\right)" if term.subs(x, 1) > 0
                      else f"-{op} \\left( {sym.latex(-term, **kwargs)} \\right)") for term in term_list[1:]]

    return "".join(expanded)


class MyLatexPrinter(LatexPrinter):
    """
    Print polynomials without some of the auto-formatting sym.latex gives.
    Used for the polytex and add_terms functions below.
    This modifies the built-in sympy LatexPrinter class by changing how Pow and Mul objects get printed.
    """

    def __init__(self, settings=None):
        super().__init__(settings)
        self._settings['fold_frac_powers'] = True

    def _print_Pow(self, expr):
        if expr.exp.is_Rational and expr.exp.q != 1 and self._settings['fold_frac_powers']:
            base, p, q = self._print(expr.base), expr.exp.p, expr.exp.q
            if '^' in base and expr.base.is_Symbol:
                base = r"\left(%s\right)" % base
            if expr.base.is_Function:
                return self._print(expr.base, exp="%s/%s" % (p, q))
            return r"%s^{%s/%s}" % (base, p, q)

        tex = r"%s^{%s}"
        exp = self._print(expr.exp)
        base = self._print(expr.base)

        return tex % (base, exp)

    def _print_Mul(self, expr):
        include_parens = False
        if _coeff_isneg(expr):
            expr = -expr
            tex = "- "
            if expr.is_Add:
                tex += "("
                include_parens = True
        else:
            tex = ""

        if not expr.is_Mul:
            return tex + self._print(expr)

        for term in expr.args:
            if abs(term) != 1:
                if term.is_Add:
                    tex += f"\\left({self._print(term)}\\right)"
                else:
                    tex += self._print(term)
            elif term < 0:
                tex += "-"

        if include_parens:
            tex += ")"
        return tex


def add_terms(*args, **kwargs):
    """Like polytex but keeps the terms ordered. For example
    add_terms(f = 2 * x ** (sym.sympify(1) / 4) - (sym.sympify(1) / 2) * x ** (sym.sympify(-2) / 3) - 4 + 3 * x ** 3)
    gives 2x^{1/4} - \frac{1}{2}x^{-2/3} - 4 + 3x^{3}"""
    return polytex(sym.Add(*args, evaluate=False), order='none', **kwargs)


def polytex(expr, **kwargs):
    """
    Use to print a polynomial with none of the extra formatting that sym.latex() gives.
    For example
    polytex(f = 2 * x ** (sym.sympify(1) / 4) - (sym.sympify(1) / 2) * x ** (sym.sympify(-2) / 3) - 4 + 3 * x ** 3)
    gives 2x^{1/4} + 3x^{3} - 4 - \frac{1}{2}x^{-2/3}
    """
    return MyLatexPrinter(kwargs).doprint(expr)


def substitute(eval_point, poly, x=sym.symbols('x'), include_parentheses=True, color=None, **kwargs):
    """
    Gives the string you would achieve by substituting eval_point into poly without simplifying it
    :param eval_point: the value being substituted into poly
    :param poly: a polynomial
    :param x: the symbol being replaced
    :param include_parentheses: whether to put parentheses around the argument being substituted
    :param order: how the terms are ordered, 'lex' is default (which puts things from highest power to lowest)
    other options are 'none' and 'old' but not sure how those work exactly
    :return: a string of latex representing the substitution of eval_point into poly
    """

    # The asterisks are to avoid any issues when the color name shares a letter with the variable
    x_string = "**" + sym.latex(x) + "**"
    string_of_eval = polytex(eval_point)
    string_of_eval = string_of_eval.replace(" ", "")
    if color:
        if include_parentheses:
            string_of_eval = '\\color{%s}{\\left(%s\\right)}' % (color, string_of_eval)
        else:
            string_of_eval = '\\color{%s}{%s}' % (color, string_of_eval)
    else:
        if include_parentheses:
            string_of_eval = '\\left(%s\\right)' % string_of_eval
        else:
            string_of_eval = '%s' % string_of_eval

    function_string = polytex(poly, **kwargs).replace(sym.latex(x), x_string)
    return function_string.replace(x_string, string_of_eval)


def round(a, n, places=None):
    if places is None:
        places = n
    multiplier = 10 ** n
    if a == 0:
        num = 0
    elif a > 0:
        num = 1.0 * sym.floor(a * multiplier + 0.5) / multiplier
    else:
        num = 1.0 * sym.ceiling(a * multiplier - 0.5) / multiplier
    return f"{num:.{places}f}"


def poly_slicer(poly, first_n_terms=None, show_zeros=True, ghost_terms=True, underline=False,
                x=sym.symbols('x')):
    """Helper Function for Polynomial long division"""
    if show_zeros:
        terms = sym.Poly(poly, x).all_terms()
    else:
        terms = sym.Poly(poly, x).terms()

    first_n_terms = len(terms) if (first_n_terms is None or first_n_terms > len(terms)) else first_n_terms

    if underline:
        poly_string = f"\\underline{{ \\left({pmsign(terms[0][1], leading=True)}{sym.latex(x ** terms[0][0][0])}"

        for term in terms[1:first_n_terms]:
            poly_string += f"{constant_sign(term[1])}" \
                           f"{sym.latex(x ** term[0][0]) if term[0][0] != 0 else ''}"

        poly_string += " \\right)}"
    else:
        poly_string = f"{pmsign(terms[0][1], leading=True)}" \
                      f"{sym.latex(x ** terms[0][0][0]) if terms[0][0][0] != 0 else ''}"

        for term in terms[1:first_n_terms]:
            poly_string += f"{constant_sign(term[1])}" \
                           f"{sym.latex(x ** term[0][0]) if term[0][0] != 0 else ''}"

    if ghost_terms:
        poly_string += f"\\phantom{{ { '{{}}' if not underline else ''} "
        for term in terms[first_n_terms:]:
            poly_string += f"{constant_sign(term[1])}" \
                           f"{sym.latex(x ** term[0][0]) if term[0][0] != 0 else ''}"
        poly_string += " }"

    return poly_string


def poly_long_div(n, d, x=sym.symbols('x')):
    """
    function n / d:
        require d ≠ 0
        q ← 0
        r ← n       # At each step n = d × q + r
        while r ≠ 0 AND degree(r) ≥ degree(d):
        t ← lead(r)/lead(d)     # Divide the leading terms
         q ← q + t
         r ← r − t * d
    return (q, r)
    :return: LaTeX for polynomial long division n / d
    """
    n = sym.Poly(n, x)
    d = sym.Poly(d, x)

    q = sym.div(n, d)[0]

    long_div_string = f"\\require{{enclose}}" \
                      f"\\begin{{array}}{{r}}" \
                      f"{sym.latex(q.as_expr())} \\\\[-3pt] " \
                      f"{sym.latex(d.as_expr())} \\enclose{{longdiv}}{{{poly_slicer(n)}}}"

    term_length = len(d.all_terms())

    q = 0
    r = n
    while r != 0 and sym.degree(r) >= sym.degree(d):
        t = sym.LT(r) / sym.LT(d)
        q = q + t
        r = r - t * d

        if r == 0 or sym.degree(r) < sym.degree(d):
            long_div_string += f"\\\\[-3pt] -{poly_slicer(t * d, first_n_terms=term_length, underline=True)}" \
                               f"\\\\[-3pt] {poly_slicer(r, show_zeros=False)}"
        else:
            long_div_string += f"\\\\[-3pt] -{poly_slicer(t * d, first_n_terms=term_length, underline=True)}" \
                               f"\\\\[-3pt] {poly_slicer(r, first_n_terms=term_length)}"

    return f"{long_div_string} \\end{{array}}"


"""
These scripts must be injected in the <head> of the output HTML files in order to render LaTeX.
"""
mathjax_scripts = """
<script type="text/x-mathjax-config">
    MathJax.Ajax.config.path['a11y'] = 'https://config/TeX-AMS-MML_HTMLorMML.js/extensions/a11y';
            MathJax.Ajax.config.root = 'https://d1873o2okbzyn2.cloudfront.net/mathjax/2.7';

            MathJax.Hub.Config({
                root: 'https://d1873o2okbzyn2.cloudfront.net/mathjax/2.7',
                config: ['https://d1873o2okbzyn2.cloudfront.net/mathjax/2.7/config/TeX-AMS-MML_HTMLorMML.js'],
                renderer: 'HTML-CSS',
                extensions: ['[a11y]/accessibility-menu.js'],
                tex2jax: {
                    inlineMath: [['$_','$_']]
                },
                // This extension allows us to use extensions without require. It creates a mapping
                // from command -> extension and will load the extension on first use.
                // http://docs.mathjax.org/en/latest/tex.html#autoload-all
                TeX: {
                    extensions: ['autoload-all.js'],
                    Macros: {
                        abs: ["{\\\\left \\\\vert #1 \\\\right \\\\vert}", 1],
                        degree: ["{^\\\\circ}"],
                        longdiv: ["{\\\\enclose{longdiv}{#1}}", 1],
                        atomic: ["{_{#1}^{#2}}", 2],
                        polyatomic: ["{_{#2}{}^{#1}}", 2],
                        circledot: ["{\\\\odot}"],
                        parallelogram: ["\\\\unicode{x25B1}"],
                        ngtr: ["\\\\unicode{x226F}"],
                        nless: ["\\\\unicode{x226E}"]
                    },
                    noUndefined: {
                        // Don't swallow invalid control sequences, as the content is useless to
                        // the user if only partially rendered.
                        // Instead treat it like an error (and log it)
                        disabled: true
                    },
                },
                errorSettings: {
                    message: ['Oops, there was an error. Please reload the page.']
                },
                showProcessingMessages: false,
                'fast-preview': { disabled: true },
                AssistiveMML: { disabled: true },
            });

            // Lower mathjax processing delays so that LaTeX is rendered faster.
            // In large quizzes, it can take a very long time to load everything without this.
            // Why not 0? Because it can make the browser feel a bit unresponsive. It makes MathJax
            // rendering pretty much synchronous.
            MathJax.Hub.processSectionDelay = 1;
            MathJax.Hub.processUpdateTime = 1;
            MathJax.Hub.processUpdateDelay = 1;

            MathJax.Hub.Register.MessageHook('TeX Jax - parse error', function(message) {
                console.error('Mathjax tex error', {
                    error: message && message[1],
                    badLaTex: message && message[2],
                    lastError: MathJax.Hub.lastError,
                    internalIssueId: 'CE-1850',
                });
            });

            MathJax.Hub.Register.MessageHook('Math Processing Error', function(message) {
                console.error('Mathjax processing error', {
                    error: message && message[2],  // This will become MathJax.Hub.lastError
                    internalIssueId: 'CE-1849',
                });
            });

            MathJax.Hub.Register.MessageHook('file load error', function(message) {
                console.error('File loading error', {
                    path: message && message[1],
                    internalIssueId: 'CE-3552',
                });
            });

            // Our content does not expect the LaTeX color extension to be applied by default,
            // so remove it from autoload-all and restore the MathJax default behavior.
            MathJax.Hub.Register.StartupHook("TeX autoload-all Ready", function () {
                var MACROS = MathJax.InputJax.TeX.Definitions.macros;
                MACROS.color = "Color";
                delete MACROS.colorbox;
                delete MACROS.fcolorbox;
            });
</script>
<script src='https://d1873o2okbzyn2.cloudfront.net/mathjax/2.7/MathJax.js'></script>
"""
