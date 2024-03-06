import unittest

from prolothar_ca.model.sat.cnf import CnfFormula, CnfDisjunction
from prolothar_ca.model.sat.term import Term
from prolothar_ca.model.sat.variable import Variable, Value
from prolothar_ca.solver.sat.modelcount.polynomial_upper_bound import PolynomialUpperBound

class TestPolynomialUpperBound(unittest.TestCase):

    def test_count_example1_from_paper(self):
        a1 = Variable(1)
        a2 = Variable(2)
        a3 = Variable(3)
        cnf = CnfFormula(disjunctions=set([
            CnfDisjunction((
                Term(a1),
                Term(a2, True),
            )),
            CnfDisjunction((
                Term(a1, True),
                Term(a2, True),
                Term(a3, True),
            )),
            CnfDisjunction((
                Term(a2),
                Term(a3),
            )),
        ]))
        self.assertEqual(3, PolynomialUpperBound().count(cnf))

    def test_count_example2_from_paper(self):
        a1 = Variable(1)
        a2 = Variable(2)
        a3 = Variable(3)
        a4 = Variable(4)
        cnf = CnfFormula(disjunctions=set([
            CnfDisjunction((
                Term(a1, True),
                Term(a3),
                Term(a4, True)
            )),
            CnfDisjunction((
                Term(a1),
                Term(a3, True),
                Term(a4)
            )),
            CnfDisjunction((
                Term(a1),
                Term(a2)
            )),
            CnfDisjunction((
                Term(a1, True),
                Term(a2, True)
            )),
            CnfDisjunction((
                Term(a2, True),
                Term(a3, True)
            )),
            CnfDisjunction((
                Term(a2, True),
                Term(a3),
                Term(a4, True)
            )),
            CnfDisjunction((
                Term(a1, True),
                Term(a2),
                Term(a4, True)
            )),
            CnfDisjunction((
                Term(a2),
                Term(a4)
            ))
        ]))
        self.assertEqual(4, PolynomialUpperBound().count(cnf))

    def test_count_all_variables_present_in_cnf(self):
        x1 = Variable(1, Value.TRUE)
        cnf = CnfFormula(disjunctions=set([
            CnfDisjunction((
                Term(x1),
                Term(Variable(2, Value.FALSE)),
                Term(Variable(3, Value.FALSE)),
            )),
            CnfDisjunction((
                Term(x1),
            ))
        ]))
        self.assertEqual(5, PolynomialUpperBound().count(cnf))

    def test_count_not_all_variables_present_in_cnf(self):
        x2 = Variable(2, Value.TRUE)
        cnf = CnfFormula(disjunctions=set([
            CnfDisjunction((
                Term(x2),
                Term(Variable(3, Value.FALSE)),
                Term(Variable(4, Value.TRUE)),
            )),
            CnfDisjunction((
                Term(x2),
            ))
        ]))
        self.assertEqual(9, PolynomialUpperBound().count(cnf))

    def test_count_unsatisfiable(self):
        variable = Variable(1, Value.TRUE)
        cnf = CnfFormula(disjunctions=set([
            CnfDisjunction((
                Term(variable),
            )),
            CnfDisjunction((
                Term(variable, negated=True),
            ))
        ]))
        self.assertEqual(0, PolynomialUpperBound().count(cnf))

    def test_count_unsatisfiable_with_variable_not_in_cnf(self):
        variable = Variable(2, Value.TRUE)
        cnf = CnfFormula(disjunctions=set([
            CnfDisjunction((
                Term(variable),
            )),
            CnfDisjunction((
                Term(variable, negated=True),
            ))
        ]))
        #the wrong output is expected (upper bound)
        self.assertEqual(0, PolynomialUpperBound().count(cnf))

if __name__ == '__main__':
    unittest.main()