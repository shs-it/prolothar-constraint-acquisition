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

from prolothar_ca.model.pddl.problem cimport Problem
from prolothar_ca.model.pddl.state cimport State
from prolothar_ca.model.pddl.pddl_object cimport Object

cdef class CaVariableType:
    cpdef int get_value_arity(self)
    cpdef str get_sqlite_type_name(self)
    cpdef str format_value_sqlite(self, object value)
    cpdef object get_feature_value_from_pddl_state(
            self, Problem problem, State current_state, Object pddl_object,
            str feature_name)
    cpdef object get_relation_value_from_pddl_state(
            self, Problem problem, State current_state, str relation_name,
            tuple relation_parameters)

cdef class CaBoolean(CaVariableType):
    cpdef int get_value_arity(self)
    cpdef str get_sqlite_type_name(self)
    cpdef str format_value_sqlite(self, object value)
    cpdef object get_feature_value_from_pddl_state(
            self, Problem problem, State current_state, Object pddl_object,
            str feature_name)
    cpdef object get_relation_value_from_pddl_state(
            self, Problem problem, State current_state, str relation_name,
            tuple relation_parameters)

cdef class CaNumber(CaVariableType):
    cpdef int get_value_arity(self)
    cpdef str get_sqlite_type_name(self)
    cpdef str format_value_sqlite(self, object value)
    cpdef object get_feature_value_from_pddl_state(
            self, Problem problem, State current_state, Object pddl_object,
            str feature_name)
    cpdef object get_relation_value_from_pddl_state(
            self, Problem problem, State current_state, str relation_name,
            tuple relation_parameters)