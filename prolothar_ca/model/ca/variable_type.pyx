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

cdef class CaVariableType:
    cpdef int get_value_arity(self):
        raise NotImplementedError()
    cpdef str get_sqlite_type_name(self):
        raise NotImplementedError()
    cpdef str format_value_sqlite(self, object value):
        raise NotImplementedError()
    cpdef object get_feature_value_from_pddl_state(
            self, Problem problem, State current_state, Object pddl_object,
            str feature_name):
        raise NotImplementedError()
    cpdef object get_relation_value_from_pddl_state(
            self, Problem problem, State current_state, str relation_name,
            tuple relation_parameters):
        raise NotImplementedError()

cdef class CaBoolean(CaVariableType):
    def to_prolog_example(self, relation_name: str, relation_objects: list, relation_value: bool):
            return f'{relation_name}({",".join(o.object_id for o in relation_objects)})'

    def to_prolog_fact(self, relation_name: str, relation_objects: list, relation_value: bool):
        if relation_value:
            return f'{relation_name}({",".join(o.object_id for o in relation_objects)})'
        else:
            return ''

    cpdef int get_value_arity(self):
        return 0

    cpdef str get_sqlite_type_name(self):
        return 'INTEGER'

    cpdef str format_value_sqlite(self, object value):
        return '1' if value else '0'

    cpdef object get_feature_value_from_pddl_state(
            self, Problem problem, State current_state, Object pddl_object,
            str feature_name):
        return current_state.is_predicate_true(
            problem.get_domain().get_predicate_by_name(feature_name), (pddl_object,))

    cpdef object get_relation_value_from_pddl_state(
            self, Problem problem, State current_state, str relation_name,
            tuple relation_parameters):
        return current_state.is_predicate_true(
            problem.get_domain().get_predicate_by_name(relation_name), relation_parameters)

    def __repr__(self) -> str:
        return 'Boolean'

cdef class CaNumber(CaVariableType):
    def to_prolog_example(self, relation_name: str, relation_objects: list, relation_value: float|int):
        raise NotImplementedError()

    def to_prolog_fact(self, relation_name: str, relation_objects: list, relation_value: float|int):
        if relation_value == round(relation_value):
            relation_value_str = str(round(relation_value))
        else:
            relation_value_str = relation_value
        return f'{relation_name}({",".join(o.object_id for o in relation_objects)},{relation_value_str})'

    cpdef int get_value_arity(self):
        return 1

    cpdef str get_sqlite_type_name(self):
        return 'REAL'

    cpdef str format_value_sqlite(self, object value):
        return str(value)

    cpdef object get_feature_value_from_pddl_state(
            self, Problem problem, State current_state, Object pddl_object,
            str feature_name):
        return current_state.get_numeric_fluent_value(
            problem.get_domain().get_numeric_fluent_by_name(feature_name), (pddl_object,))

    cpdef object get_relation_value_from_pddl_state(
            self, Problem problem, State current_state, str relation_name,
            tuple relation_parameters):
        return current_state.is_predicate_true(
            problem.get_domain().get_numeric_fluent_by_name(relation_name), relation_parameters)

    def __repr__(self) -> str:
        return 'Number'