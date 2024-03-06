import unittest

from prolothar_ca.model.sat.cnf import CnfFormula, CnfDisjunction
from prolothar_ca.model.sat.term import Term
from prolothar_ca.model.sat.variable import Variable
from prolothar_ca.solver.sat.solver.twosat_solver import TwoSatSolver

class TestTwoSatSolver(unittest.TestCase):

    def test_solve_all_variables_present_in_cnf(self):
        variable_1 = Variable(1)
        cnf = CnfFormula(disjunctions=set([
            CnfDisjunction((
                Term(variable_1),
                Term(Variable(2)),
                Term(Variable(3)),
            )),
            CnfDisjunction((
                Term(variable_1),
            ))
        ]))
        self.assertTrue(TwoSatSolver().is_cnf_satisfiable(cnf))
        solution = TwoSatSolver().solve_cnf(cnf)
        self.assertIsNotNone(solution)

    def test_solve_not_all_variables_present_in_cnf(self):
        variable_1 = Variable(1)
        cnf = CnfFormula(disjunctions=set([
            CnfDisjunction((
                Term(variable_1),
                Term(Variable(3)),
            )),
            CnfDisjunction((
                Term(variable_1),
            ))
        ]))
        self.assertTrue(TwoSatSolver().is_cnf_satisfiable(cnf))
        solution = TwoSatSolver().solve_cnf(cnf)
        self.assertIsNotNone(solution)

    def test_recognize_unsatisfiable(self):
        variable_2 = Variable(2)
        cnf = CnfFormula(disjunctions=set([
            CnfDisjunction((
                Term(variable_2),
            )),
            CnfDisjunction((
                Term(variable_2, negated=True),
            ))
        ]))
        self.assertFalse(TwoSatSolver().is_cnf_satisfiable(cnf))
        solution = TwoSatSolver().solve_cnf(cnf)
        self.assertIsNone(solution)

if __name__ == '__main__':
    unittest.main()