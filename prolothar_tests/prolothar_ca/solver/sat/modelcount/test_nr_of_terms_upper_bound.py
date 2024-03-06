import unittest
from math import log2

from prolothar_ca.model.sat.cnf import CnfFormula, CnfDisjunction
from prolothar_ca.model.sat.term import Term
from prolothar_ca.model.sat.variable import Variable, Value
from prolothar_ca.solver.sat.modelcount.nr_of_terms_upper_bound import NrOfTermsUpperBound

class TestNrOfTermsUpperBound(unittest.TestCase):

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
        #there is exactly one solution, so 0 is a valid lower bound
        self.assertEqual(8, NrOfTermsUpperBound().count(cnf))
        self.assertEqual(log2(NrOfTermsUpperBound().count(cnf)), NrOfTermsUpperBound().countlog2(cnf))

if __name__ == '__main__':
    unittest.main()