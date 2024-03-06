import unittest

from prolothar_ca.model.sat.cnf import CnfFormula, CnfDisjunction
from prolothar_ca.model.sat.term import Term
from prolothar_ca.model.sat.variable import Variable, Value
from prolothar_ca.solver.sat.modelcount.quadratic_variable_elimination import QuadraticVariableElimination

class TestQuadraticVariableElimination(unittest.TestCase):

    def test_count_example1_from_paper(self):
        a1 = Variable(1, Value.TRUE)
        a2 = Variable(2, Value.FALSE)
        a3 = Variable(3, Value.TRUE)
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
        self.assertEqual(cnf.value(), Value.TRUE)
        self.assertGreaterEqual(3, QuadraticVariableElimination().count(cnf))
        self.assertEqual(2, QuadraticVariableElimination().count(cnf))

    def test_count_example2_from_paper(self):
        a1 = Variable(1, Value.FALSE)
        a2 = Variable(2, Value.TRUE)
        a3 = Variable(3, Value.FALSE)
        a4 = Variable(4, Value.FALSE)
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
        self.assertEqual(cnf.value(), Value.TRUE)
        self.assertEqual(2, QuadraticVariableElimination().count(cnf))

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
        self.assertEqual(cnf.value(), Value.TRUE)
        self.assertEqual(4, QuadraticVariableElimination().count(cnf))

if __name__ == '__main__':
    unittest.main()