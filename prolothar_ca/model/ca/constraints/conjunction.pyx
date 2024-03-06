'''
    This file is part of Prolothar-Constraint-Acquisition (More Info: https://github.com/shs-it/prolothar-constraint-acquisition).

    Prolothar-Constraint-Acquisition is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Prolothar-Constraint-Acquisition is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Prolothar-Constraint-Acquisition. If not, see <https://www.gnu.org/licenses/>.
'''

from dataclasses import dataclass
from typing import Generator

from prolothar_ca.model.ca.constraints.constraint import CaConstraint
from prolothar_ca.model.ca.example import CaExample
from prolothar_ca.model.ca.obj import CaObject

cdef class And(CaConstraint):
    def __init__(self, list term_list):
        self.term_list = term_list

    cpdef bint holds(self, CaExample example, dict variables):
        for term in self.term_list:
            if not (<CaConstraint>term).holds(example, variables):
                return False
        return True

    def is_more_restrictive(self, other: CaConstraint) -> bool:
        return other in self.term_list or (
            isinstance(other, And) and set(other.term_list).issubset(self.term_list)
        )

    def __hash__(self) -> int:
        return hash(str(self))

    def __str__(self) -> str:
        return f'({" and ".join(str(t) for t in self.term_list)})'

    def count_nr_of_terms(self) -> int:
        return sum(term.count_nr_of_terms() for term in self.term_list)

    def count_nr_of_preconditions(self) -> int:
        return sum(term.count_nr_of_preconditions() for term in self.term_list)

cdef class Or(CaConstraint):
    def __init__(self, list term_list):
        self.term_list = term_list

    cpdef bint holds(self, CaExample example, dict variables):
        for term in self.term_list:
            if (<CaConstraint>term).holds(example, variables):
                return True
        return False

    def is_more_restrictive(self, other: CaConstraint) -> bool:
        return isinstance(other, Or) and set(self.term_list).issubset(other.term_list)

    def count_nr_of_terms(self) -> int:
        return sum(term.count_nr_of_terms() for term in self.term_list)

    def count_nr_of_preconditions(self) -> int:
        return sum(term.count_nr_of_preconditions() for term in self.term_list)

    def __hash__(self) -> int:
        return hash(str(self))

    def __str__(self) -> str:
        return f'({" or ".join(str(t) for t in self.term_list)})'

cdef class Implies(CaConstraint):

    def __init__(self, CaConstraint antecedent, CaConstraint consequent):
        self.__antecedent = antecedent
        self.__consequent = consequent

    cpdef bint holds(self, CaExample example, dict variables):
        return not self.__antecedent.holds(example, variables) or self.__consequent.holds(example, variables)

    def is_more_restrictive(self, other: CaConstraint) -> bool:
        return isinstance(other, Or) and self in other.term_list

    def count_nr_of_terms(self) -> int:
        return self.__antecedent.count_nr_of_terms() + self.__consequent.count_nr_of_terms()

    def count_nr_of_preconditions(self) -> int:
        return self.__antecedent.count_nr_of_preconditions()

    def __hash__(self) -> int:
        return hash(str(self))

    def __str__(self) -> str:
        return f'{self.__antecedent} -> {self.__consequent}'

    def __eq__(self, other):
        return (
            isinstance(other, Implies) and
            self.__antecedent == other.__antecedent and
            self.__consequent == other.__consequent
        )
