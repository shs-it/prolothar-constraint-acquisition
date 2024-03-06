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

from prolothar_ca.model.pddl.condition cimport Condition
from prolothar_ca.model.pddl.numeric_expression cimport NumericExpression
from prolothar_ca.model.pddl.object_type cimport ObjectType


cdef class Effect:
    cpdef modify_state(self, dict parameter_assignment, object state)

cdef class SetPredicateTrue(Effect):
    cdef object __predicate
    cdef list __parameter_names

cdef class SetPredicateFalse(Effect):
    cdef object __predicate
    cdef list __parameter_names

cdef class DecreaseEffect(Effect):
    cdef object __numeric_fluent
    cdef list __parameter_names
    cdef NumericExpression __value

cdef class IncreaseEffect(Effect):
    cdef object __numeric_fluent
    cdef list __parameter_names
    cdef NumericExpression __value

cdef class SetNumericFluent(Effect):
    cdef object __numeric_fluent
    cdef list __parameter_names
    cdef NumericExpression __value

cdef class ForAllEffect(Effect):
    cdef str __parameter_name
    cdef ObjectType __parameter_type
    cdef Effect __effect

cdef class When(Effect):
    cdef Condition __condition
    cdef Effect __effect

cdef class AndEffect(Effect):
    cdef list __effect_list