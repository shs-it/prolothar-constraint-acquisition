import unittest

from prolothar_ca.model.sat.cnf import CnfFormula, CnfDisjunction
from prolothar_ca.model.sat.term import Term
from prolothar_ca.model.sat.variable import Variable
from prolothar_ca.solver.sat.modelcount.mc2 import MC2

class TestMC2(unittest.TestCase):

    def test_count_all_variables_present_in_cnf(self):
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
        self.assertEqual(4, MC2().count(cnf))

    def test_count_more_than_four_variables(self):
        variable_1 = Variable(1)
        variable_2 = Variable(2)
        variable_3 = Variable(3)
        variable_4 = Variable(4)
        variable_5 = Variable(5)
        variable_6 = Variable(6)
        cnf = CnfFormula(disjunctions=set([
            CnfDisjunction((
                Term(variable_1),
                Term(variable_2),
            )),
            CnfDisjunction((
                Term(variable_3),
                Term(variable_4),
            )),
            CnfDisjunction((
                Term(variable_5),
                Term(variable_6),
            )),
        ]))
        self.assertEqual(27, MC2().count(cnf))

    def test_count_more_than_four_variables_no_disjunction(self):
        variable_1 = Variable(1)
        variable_2 = Variable(2)
        variable_3 = Variable(3)
        variable_4 = Variable(4)
        variable_5 = Variable(5)
        variable_6 = Variable(6)
        cnf = CnfFormula(disjunctions=set([
            CnfDisjunction((
                Term(variable_1),
                Term(variable_2),
            )),
            CnfDisjunction((
                Term(variable_1),
                Term(variable_3),
            )),
            CnfDisjunction((
                Term(variable_1),
                Term(variable_4),
            )),
            CnfDisjunction((
                Term(variable_1),
                Term(variable_5),
            )),
            CnfDisjunction((
                Term(variable_1),
                Term(variable_6, negated=True),
            )),
        ]))
        #actual value is 2**5+1, but we accept this lower bound
        self.assertEqual(2**5, MC2().count(cnf))

    def test_count_unsatisfiable(self):
        variable_2 = Variable(2)
        cnf = CnfFormula(disjunctions=set([
            CnfDisjunction((
                Term(variable_2),
            )),
            CnfDisjunction((
                Term(variable_2, negated=True),
            ))
        ]))
        self.assertEqual(0, MC2().count(cnf))

if __name__ == '__main__':
    unittest.main()