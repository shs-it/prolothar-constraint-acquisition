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

from dataclasses import dataclass, field
from prolothar_ca.model.ca.variable_type import CaVariableType

cdef class CaRelation:
    def __init__(self, str name, tuple objects, object value):
        self.name = name
        self.objects = objects
        self.value = value
        self.__hash = hash((name, objects, value))

    def __hash__(self):
        return self.__hash

    def __eq__(self, other: 'CaRelation'):
        return other.name == self.name and self.objects == other.objects and self.value == other.value

    def __repr__(self):
        return f'CaRelation({self.name}, {self.objects}, {self.value})'

cdef class CaRelationType:
    def __init__(self, str name, tuple parameter_types, value_type: CaVariableType):
        self.name = name
        self.parameter_types = parameter_types
        self.value_type = value_type

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other: 'CaRelationType'):
        return self.name == other.name and self.parameter_types == other.parameter_types and self.value_type == other.value_type

    def to_prolog_example(self, relation: CaRelation) -> str:
        return self.value_type.to_prolog_example(self.name, relation.objects, relation.value)

    def to_prolog_fact(self, relation: CaRelation) -> str:
        return self.value_type.to_prolog_fact(self.name, relation.objects, relation.value)

    def __repr__(self):
        return f'CaRelationType({self.name}, {self.parameter_types}, {self.value_type})'
