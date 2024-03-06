import unittest

from prolothar_ca.model.sat.variable import Value
from prolothar_ca.model.sat.variable import Variable
from prolothar_ca.model.sat.term import Term
from prolothar_ca.model.sat.cnf import CnfDisjunction

class TestCnfDisjunction(unittest.TestCase):

    def test_term(self):
        self.assertNotEqual(Value.UNKNOWN, Value.TRUE)
        self.assertNotEqual(Value.UNKNOWN, Value.FALSE)
        self.assertNotEqual(Value.TRUE, Value.FALSE)

        x1 = Variable(1)
        x2 = Variable(2)

        disjunction = CnfDisjunction((Term(x1), Term(x2)))
        self.assertEqual(Value.UNKNOWN, disjunction.value())

        x1.value = Value.TRUE
        self.assertEqual(Value.TRUE, disjunction.value())

        x1.value = Value.FALSE
        self.assertEqual(Value.UNKNOWN, disjunction.value())

        x2.value = Value.TRUE
        self.assertEqual(Value.TRUE, disjunction.value())

        x2.value = Value.FALSE
        self.assertEqual(Value.FALSE, disjunction.value())

if __name__ == '__main__':
    unittest.main()