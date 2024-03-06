import unittest

from prolothar_ca.model.sat.variable import Variable, Value
from prolothar_ca.model.sat.term import Term

class TestTerm(unittest.TestCase):

    def test_term(self):
        x = Variable(1)
        term = Term(x)
        negated_term = Term(x, negated=True)
        self.assertEqual(Value.UNKNOWN, term.value())
        self.assertEqual(Value.UNKNOWN, negated_term.value())

        x.value = Value.TRUE
        self.assertEqual(Value.TRUE, term.value())
        self.assertEqual(Value.FALSE, negated_term.value())

        x.value = Value.FALSE
        self.assertEqual(Value.TRUE, negated_term.value())
        self.assertEqual(Value.FALSE, term.value())

if __name__ == '__main__':
    unittest.main()