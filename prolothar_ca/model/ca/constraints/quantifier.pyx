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

cdef class ForAll(CaConstraint):
    query: Query
    constraint: CaConstraint
    def __init__(self, Query query, CaConstraint constraint):
        self.query = query
        self.constraint = constraint

    cpdef bint holds(self, CaExample example, dict variables):
        cdef dict extended_variables
        for element in self.query.evaluate(example, variables):
            extended_variables = dict(variables)
            extended_variables.update(<dict>element)
            if not self.constraint.holds(example, extended_variables):
                return False
        return True

    def is_more_restrictive(self, other: CaConstraint) -> bool:
        return (
            isinstance(other, ForAll) and
            self.query == other.query and
            self.constraint.is_more_restrictive(other.constraint)
        )

    def __str__(self) -> str:
        return f'for all {self.query}: {self.constraint}'

    def count_nr_of_terms(self) -> int:
        return self.query.count_nr_of_terms() + self.constraint.count_nr_of_terms()

    def count_nr_of_preconditions(self) -> int:
        return self.query.count_nr_of_preconditions()
