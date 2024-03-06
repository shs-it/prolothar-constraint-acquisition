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

from prolothar_ca.model.pddl.numeric_expression cimport NumericExpression
from prolothar_ca.model.pddl.object_type cimport ObjectType


cdef class Condition:
    cpdef bint holds(self, dict parameter_assignment, state, problem)

cdef class PredicateIsTrueCondition(Condition):
    cdef object __predicate
    cdef list __parameter_names

cdef class Greater(Condition):
    cdef NumericExpression __expression_a
    cdef NumericExpression __expression_b

cdef class GreaterOrEqual(Condition):
    cdef NumericExpression __expression_a
    cdef NumericExpression __expression_b

cdef class Less(Condition):
    cdef NumericExpression __expression_a
    cdef NumericExpression __expression_b

cdef class LessOrEqual(Condition):
    cdef NumericExpression __expression_a
    cdef NumericExpression __expression_b

cdef class Equals(Condition):
    cdef NumericExpression __expression_a
    cdef NumericExpression __expression_b

cdef class Not(Condition):
    cdef Condition __condition

cdef class Or(Condition):
    cdef list __condition_list

cdef class And(Condition):
    cdef list __condition_list

cdef class Exists(Condition):
    cdef str __parameter_name
    cdef ObjectType __parameter_type
    cdef Condition __condition

cdef class ForAll(Condition):
    cdef str __parameter_name
    cdef ObjectType __parameter_type
    cdef Condition __condition
