import unittest

from prolothar_ca.model.sat.cnf import CnfFormula, CnfDisjunction
from prolothar_ca.model.sat.term import Term
from prolothar_ca.model.sat.variable import Variable

class TestCnfFormula(unittest.TestCase):

    def test_fix_variable(self):
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

        self.assertEqual(5, cnf.get_nr_of_clauses())
        self.assertEqual(0, cnf.fix_variable(variable_1, True).get_nr_of_clauses())
        self.assertEqual(CnfFormula(disjunctions=set([
            CnfDisjunction((
                Term(variable_2),
            )),
            CnfDisjunction((
                Term(variable_3),
            )),
            CnfDisjunction((
                Term(variable_4),
            )),
            CnfDisjunction((
                Term(variable_5),
            )),
            CnfDisjunction((
                Term(variable_6, negated=True),
            )),
        ])), cnf.fix_variable(variable_1, False))

        self.assertEqual(5, cnf.fix_variable(variable_6, True).get_nr_of_clauses())
        self.assertEqual(4, cnf.fix_variable(variable_6, False).get_nr_of_clauses())

        self.assertEqual(4, cnf.fix_variable(variable_5, True).get_nr_of_clauses())
        self.assertEqual(5, cnf.fix_variable(variable_5, False).get_nr_of_clauses())

    def test_has_overlap(self):
        variable_1 = Variable(1)
        variable_2 = Variable(2)
        variable_3 = Variable(3)
        variable_4 = Variable(4)
        variable_5 = Variable(5)
        variable_6 = Variable(6)
        cnf_a = CnfFormula(disjunctions=set([
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
        cnf_b = CnfFormula(disjunctions=set([
            CnfDisjunction((
                Term(variable_1),
                Term(variable_2),
            ))
        ]))
        cnf_c = CnfFormula(disjunctions=set([
            CnfDisjunction((
                Term(variable_2),
                Term(variable_3),
            ))
        ]))
        self.assertTrue(cnf_a.has_overlap(cnf_b))
        self.assertTrue(cnf_b.has_overlap(cnf_a))
        self.assertFalse(cnf_b.has_overlap(cnf_c))
        self.assertFalse(cnf_c.has_overlap(cnf_b))

if __name__ == '__main__':
    unittest.main()