import random
import sympy as sym
import tools
from tools import unique, Printer, Template, Problem
import validations
import os
import sys

class Template1(Template):
    """Template for generating problems of the form ax^{n} where n is rational and a is a non-zero integer"""
    @unique
    def variables(self):
        # Define any variables you need here. The @unique decorator will ensure your variables are unique
        a = tools.non_zero_select(-10, 10)
        num = tools.non_zero_select(-10, 10)
        denom = tools.non_zero_select(2, 10)
        n = sym.Rational(num, denom)

        assert a != 1  # assures a non-trivial coefficient
        assert num % denom != 0  # prevents an integer exponent

        return a, n

    def template(self):
        x = sym.symbols('x')
        a, n = self.variables()

        f = a * x ** n
        df = sym.diff(f)

        df_string = tools.polytex(df)  # You can use sym.polytex or tools.latex to get the LaTeX for a sympy expression.
        f_string = tools.polytex(f)

        question_stem = f"Find $_\\displaystyle \\frac{{d}}{{dx}} \\left({f_string}\\right)$_. "

        # Recall
        explanation = f"<p>To solve this problem, you will need to recall:" \
                      f"<ul>" \
                      f"<li>The <b>extended power rule</b> for derivatives states that if $_f(x) = x^n$_, " \
                      f"and $_n$_ " \
                      f"is a non-zero real number, then" \
                      f"$$\\frac{{d}}{{dx}}f(x)= n x^{{n-1}}.$$</li>" \
                      f"<li>The <b>constant multiple rule</b> for derivatives states that the derivative of a " \
                      f"constant times a function is equal to the constant times the derivative of the function. " \
                      f"In math notation this means that if $_g(x) = cf(x)$_, where $_c$_ is a constant, then" \
                      f"$$\\frac{{d}}{{dx}}\\left(g(x)\\right) = c \\frac{{d}}{{dx}}\\left( f(x) \\right).$$</li>" \
                      f"</ul></p>"

        explanation += f"<p>In this problem we are given $_f(x) = {f_string}$_. We can use the constant rule to " \
                       f"take the constant, $_{a}$_ outside of the derivative to find" \
                       f"$$\\begin{{align}}" \
                       f"\\frac{{d}}{{dx}} f(x) &= \\frac{{d}}{{dx}} \\left({f_string}\\right) \\\\[5pt]" \
                       f"&= {a} \\cdot \\frac{{d}}{{dx}} \\left(x^{{ {n} }}\\right)." \
                       f"\\end{{align}}$$ </p>" \
                       f"<p>Using the power rule to differentiate $_x^{{ {n} }} $_ we have" \
                       f"$$\\begin{{align}}" \
                       f"\\frac{{d}}{{dx}} f(x) &= {a} \\cdot \\frac{{d}}{{dx}} \\left(x^{{ {n} }}\\right) \\\\[5pt]" \
                       f"&= {a}\\left({sym.latex(n)}x^{{ {n} - 1 }}\\right) \\\\[5pt]" \
                       f"&= {df_string}." \
                       f"\\end{{align}}$$</p>"

        correct_answer = f"\\frac{{d}}{{dx}}\\left({f_string}\\right)={df_string} "
        question_template = f"\\frac{{d}}{{dx}}\\left({f_string}\\right)={{{{response}}}}"

        json_blob = validations.lea_blob(template=question_template,
                                         response=correct_answer,
                                         validation="equivSymbolic")

        return Problem(concepts="Find the derivative of a monomial function with negative exponents",
                       question_stem=question_stem,
                       explanation=explanation,
                       correct_answer=correct_answer,
                       json_blob=json_blob)


class Template2(Template):
    """Template for generating problems of the type ax^m + bx^n + c where one (or both)
    of n, m is a negative fraction."""
    @unique
    def variables(self):
        # Define any variables you need here. The @unique decorator will ensure your variables are unique
        a = tools.non_zero_select(-10, 10)
        b = random.randint(-9, 9)
        c = random.randint(-9, 9)

        m_num = tools.non_zero_select(-9, 9)
        m_denom = random.randint(2, 9)
        m = sym.Rational(m_num, m_denom)

        n_num = tools.non_zero_select(-9, 9)
        n_denom = random.randint(2, 9)
        n = sym.Rational(n_num, n_denom)

        assert a != 1  # assures a non-trivial coefficient
        assert b != 1
        assert c != 1
        assert not (b == 0 and c == 0)  # b and c cannot both be 0
        assert not (m_num % m_denom == 0 and n_num % n_denom == 0)  # only one exponent if any can be an integer
        assert not (m_num > 0 and n_num > 0)  # at least one exponent is negative
        if m_num % m_denom != 0:  # ensures a negative fractional exponent
            assert m_num < 0
        else:
            assert n_num < 0

        return a, b, c, m, n

    def template(self):
        x = sym.symbols('x')  # A sympy variable.
        a, b, c, m, n = self.variables()  # Call the variables here.

        a_term = a * x ** n
        df_a = sym.diff(a_term)
        b_term = b * x ** n
        df_b = sym.diff(b_term)
        f = a_term + b_term + c
        df = df_a + df_b

        df_string = tools.terms_string(df_a, df_b)  # You can use sym.polytex or tools.latex to get the LaTeX for a sympy expression.
        f_string = tools.polytex(tools.terms_string(a_term, b_term, c))

        a_abs_term_string = tools.polytex(abs(a) * x ** n)
        b_abs_term_string = tools.polytex(abs(b) * x ** m)
        c_abs_term_string = tools.polytex(abs(c))

        # This should contain your question string.
        question_stem = f"Find $_\\displaystyle \\frac{{d}}{{dx}} \\left({f_string}\\right)$_. "

        # This will contain the explanation.
        explanation = f"<p>To solve this problem, you will need to recall:" \
                      f"<ul>" \
                      f"<li>The <b>sum and difference rules</b> for derivatives state that the derivative of the sum " \
                      f"or difference of two functions is equal to the sum or difference of their derivative. In math" \
                      f" notation this means that if $_h(x) = f(x)\\pm g(x)$_, then" \
                      f"$$\\frac{{d}}{{dx}}(h(x))= \\frac{{d}}{{dx}}(f(x))\\pm\\frac{{d}}{{dx}}(g(x)).$$</li>" \
                      f"<li>The <b>extended power rule</b> for derivatives states that if $_f(x) = x^n$_, " \
                      f"where $_n$_ is a non-zero integer, then" \
                      f"$$\\frac{{d}}{{dx}}f(x)= n x^{{n-1}}.$$</li>" \
                      f"<li>The <b>constant multiple rule</b> for derivatives states that the derivative of a " \
                      f"constant times a function is equal to the constant times the derivative of the function. " \
                      f"In math notation this means that if $_g(x) = cf(x)$_, where $_c$_ is a constant, then" \
                      f"$$\\frac{{d}}{{dx}}\\left(g(x)\\right) = c \\frac{{d}}{{dx}}\\left( f(x) \\right).$$</li>" \
                      f"</ul></p>"

        explanation += f"<p>Applying the sum and difference rules to the given function gives " \
                       f"$$\\begin{{align}}" \
                       f"f(x) &= {f_string} \\\\[5pt] " \
                       f"\\frac{{d}}{{dx}}f(x) &= \\frac{{d}}{{dx}}\\left({f_string}\\right)" \
                       f"&= "

        if a < 0:
            explanation += f"-"
        explanation += f"\\frac{{d}}{{dx}}\\left({a_abs_term_string}\\right)"

        if b < 0:
            explanation += f"-"
        else:
            explanation += f"+"
        explanation += f"\\frac{{d}}{{dx}}\\left({b_abs_term_string}\\right)"

        if c < 0:
            explanation += f"-"
        else:
            explanation += f"+"
        explanation += f"\\frac{{d}}{{dx}}\\left({c_abs_term_string}\\right)" \
                       f"\\end{{align}}$$ </p>" \
                       f"<p>Applying the constant rule to take the constants outside of the derivatives and using the" \
                       f" fact that the derivative of a constant is zero, we have" \
                       f"\\end{{align}}$$</p>"


        #
        # explanation += f"take the constant, $_{a}$_ outside of the derivative to find" \
        #                f"$$\\begin{{align}}" \
        #                f"\\frac{{d}}{{dx}} f(x) &= \\frac{{d}}{{dx}} \\left({f_string}\\right) \\\\[5pt]" \
        #                f"&= {a} \\cdot \\frac{{d}}{{dx}} \\left(x^{{ {n} }}\\right)." \
        #                f"\\end{{align}}$$ </p>" \
        #                f"<p>Using the power rule to differentiate $_x^{{ {n} }} $_ we have" \
        #                f"$$\\begin{{align}}" \
        #                f"\\frac{{d}}{{dx}} f(x) &= {a} \\cdot \\frac{{d}}{{dx}} \\left(x^{{ {n} }}\\right) \\\\[5pt]" \
        #                f"&= {a}\\left({sym.latex(n)}x^{{ {n} - 1 }}\\right) \\\\[5pt]" \
        #                f"&= {df_string}." \
        #                f"\\end{{align}}$$</p>"

        # Fill this in with the correct answer. It should be in LaTeX notation but without any wrappers.
        correct_answer = f" "

        # You can leave this blank
        question_template = f" "

        json_blob = validations.lea_blob(template=question_template,
                                         response=correct_answer,
                                         validation="equivSymbolic")

        return Problem(concepts="Find the derivative of a function with negative exponents",
                       question_stem=question_stem,
                       explanation=explanation,
                       correct_answer=correct_answer,
                       json_blob=json_blob)


if __name__ == '__main__':
    os.chdir(sys.path[0])
    random.seed(1)
    adaptive_printer = Printer("Extend the power rule to functions with rational exponents")

    Templates = [Template1, Template2]
    adaptive_printer.print_all(*[Template().take(20) for Template in Templates])
