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

from cpython.tuple cimport PyTuple_New, PyTuple_SET_ITEM, PyTuple_GET_ITEM, PyTuple_GET_SIZE
from cpython.ref cimport Py_INCREF

from prolothar_ca.model.ca.constraints.conjunction import Or
from prolothar_ca.model.ca.constraints.constraint cimport CaConstraint
from prolothar_ca.model.ca.obj cimport CaObject
from prolothar_ca.model.ca.relation cimport CaRelationType
from prolothar_ca.model.ca.example cimport CaExample

cpdef tuple _create_relation_parameters(
        tuple object_id_list, tuple parameter_types,
        CaExample example, variables: dict[str, CaObject]):
    cdef tuple relation_parameters = PyTuple_New(PyTuple_GET_SIZE(object_id_list))
    cdef object an_object
    cdef size_t i
    for i,object_id in enumerate(object_id_list):
        try:
            an_object = variables[object_id]
        except KeyError:
            an_object = example.get_object_by_type_and_id(
                <str>PyTuple_GET_ITEM(parameter_types, i), object_id
            )
        Py_INCREF(an_object)
        PyTuple_SET_ITEM(relation_parameters, i, an_object)
    return relation_parameters

cdef class RelationIsTrue(CaConstraint):

    def __init__(self, CaRelationType relation_type, tuple object_id_list):
        self.__relation_type = relation_type
        self.__object_id_list = object_id_list

    def is_more_restrictive(self, other: CaConstraint) -> bool:
        return isinstance(other, Or) and self in other.term_list

    cpdef bint holds(self, CaExample example, dict variables):
        return example.get_boolean_relation_value(
            self.__relation_type.name, _create_relation_parameters(
                self.__object_id_list, self.__relation_type.parameter_types,
                example, variables))

    cpdef str get_relation_name(self):
        return self.__relation_type.name

    def count_nr_of_terms(self) -> int:
        return 1

    def count_nr_of_preconditions(self) -> int:
        return 1

    def __str__(self) -> str:
        return f'{self.__relation_type.name}({",".join(self.__object_id_list)})'

    def __hash__(self):
        return hash((True, self.__relation_type.name, self.__object_id_list))

    def __eq__(self, other):
        return (
            isinstance(other, RelationIsTrue) and
            self.__relation_type == other.__relation_type and
            self.__object_id_list == other.__object_id_list
        )

cdef class RelationIsFalse(CaConstraint):

    def __init__(self, CaRelationType relation_type, tuple object_id_list):
        self.__relation_type = relation_type
        self.__object_id_list = object_id_list

    def is_more_restrictive(self, other: CaConstraint) -> bool:
        return isinstance(other, Or) and self in other.term_list

    cpdef bint holds(self, CaExample example, dict variables):
        return not example.get_boolean_relation_value(
            self.__relation_type.name, _create_relation_parameters(
                self.__object_id_list, self.__relation_type.parameter_types,
                example, variables))

    def count_nr_of_terms(self) -> int:
        return 1

    def count_nr_of_preconditions(self) -> int:
        return 1

    def __str__(self) -> str:
        return f'!{self.__relation_type.name}({",".join(self.__object_id_list)})'

    def __hash__(self):
        return hash((False, self.__relation_type.name, self.__object_id_list))

    def __eq__(self, other):
        return (
            isinstance(other, RelationIsFalse) and
            self.__relation_type == other.__relation_type and
            self.__object_id_list == other.__object_id_list
        )

cdef class Not(CaConstraint):

    def __init__(self, CaConstraint constraint):
        self.__constraint = constraint

    def is_more_restrictive(self, other: CaConstraint) -> bool:
        return isinstance(other, Or) and self in other.term_list

    cpdef bint holds(self, CaExample example, dict variables):
        return not self.__constraint.holds(example, variables)

    def count_nr_of_terms(self) -> int:
        nr_of_terms_in_constraint = self.__constraint.count_nr_of_terms()
        if nr_of_terms_in_constraint == 1:
            return 1
        else:
            return 1 + nr_of_terms_in_constraint

    def count_nr_of_preconditions(self) -> int:
        nr_of_terms_in_constraint = self.__constraint.count_nr_of_preconditions()
        if nr_of_terms_in_constraint == 1:
            return 1
        else:
            return 1 + nr_of_terms_in_constraint

    def __str__(self) -> str:
        return f'!{self.__constraint}'

cdef class BooleanFeatureIsTrue(CaConstraint):
    def __init__(self, str object_type, str object_id, str feature_name):
        self.__object_type = object_type
        self.__object_id = object_id
        self.__feature_name = feature_name

    cpdef bint holds(self, CaExample example, dict variables):
        try:
            the_object = example.get_object_by_type_and_id(self.__object_type, self.__object_id)
        except KeyError:
            the_object = variables[self.__object_id]
        return <bint>((<CaObject>the_object).features[self.__feature_name])

    def is_more_restrictive(self, other: CaConstraint) -> bool:
        return isinstance(other, Or) and self in other.term_list

    def __str__(self) -> str:
        return f'{self.__object_id}.{self.__feature_name}'

    def count_nr_of_terms(self) -> int:
        return 1

    def count_nr_of_preconditions(self) -> int:
        return 1

cdef class BooleanFeatureIsFalse(CaConstraint):
    def __init__(self, object_type: str, object_id: str, feature_name: str):
        self.__object_type = object_type
        self.__object_id = object_id
        self.__feature_name = feature_name

    cpdef bint holds(self, CaExample example, dict variables):
        try:
            the_object = example.get_object_by_type_and_id(self.__object_type, self.__object_id)
        except KeyError:
            the_object = variables[self.__object_id]
        return not (<bint>(<CaObject>the_object).features[self.__feature_name])

    def is_more_restrictive(self, other: CaConstraint) -> bool:
        return isinstance(other, Or) and self in other.term_list

    def __str__(self) -> str:
        return f'!{self.__object_id}.{self.__feature_name}'

    def count_nr_of_terms(self) -> int:
        return 1

    def count_nr_of_preconditions(self) -> int:
        return 1