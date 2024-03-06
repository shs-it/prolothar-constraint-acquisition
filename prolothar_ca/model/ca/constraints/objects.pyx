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

from prolothar_ca.model.ca.constraints.conjunction import Or
from prolothar_ca.model.ca.example cimport CaExample
from prolothar_ca.model.ca.obj cimport CaObject

from prolothar_ca.model.ca.constraints.constraint import CaConstraint

cdef class ObjectsEqual(CaConstraint):
    def __init__(self, str left_object_id, str right_object_id):
        self.left_object_id = left_object_id
        self.right_object_id = right_object_id

    def is_more_restrictive(self, other: CaConstraint) -> bool:
        return isinstance(other, Or) and self in other.term_list

    cpdef bint holds(self, CaExample example, dict variables):
        cdef str left_object_id
        cdef str right_object_id
        try:
            left_object_id = (<CaObject>variables[self.left_object_id]).object_id
        except KeyError:
            left_object_id = self.left_object_id
        try:
            right_object_id = (<CaObject>variables[self.right_object_id]).object_id
        except KeyError:
            right_object_id = self.right_object_id
        return left_object_id == right_object_id

    def count_nr_of_terms(self) -> int:
        return 2

    def __str__(self) -> str:
        return f'{self.left_object_id} = {self.right_object_id}'

cdef class ObjectsNotEqual(CaConstraint):
    def __init__(self, str left_object_id, str right_object_id):
        self.left_object_id = left_object_id
        self.right_object_id = right_object_id

    def is_more_restrictive(self, other: CaConstraint) -> bool:
        return isinstance(other, Or) and self in other.term_list

    cpdef bint holds(self, CaExample example, dict variables):
        cdef str left_object_id
        cdef str right_object_id
        try:
            left_object_id = (<CaObject>variables[self.left_object_id]).object_id
        except KeyError:
            left_object_id = self.left_object_id
        try:
            right_object_id = (<CaObject>variables[self.right_object_id]).object_id
        except KeyError:
            right_object_id = self.right_object_id
        return left_object_id != right_object_id

    def count_nr_of_terms(self) -> int:
        return 2

    def __str__(self) -> str:
        return f'{self.left_object_id} != {self.right_object_id}'
