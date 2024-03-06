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

from prolothar_ca.model.ca.variable_type import CaVariableType
from prolothar_ca.model.ca.obj import CaObject

class CaRelation:
    name: str
    objects: tuple[CaObject]
    value: int|float|bool

    def __init__(self, name: str, objects: tuple, value):
        ...

class CaRelationType:
    name: str
    parameter_types: tuple[str]
    value_type: CaVariableType

    def __init__(self, name: str, parameter_types: tuple[str], value_type: CaVariableType):
        ...

    def to_prolog_example(self, relation: CaRelation) -> str:
        ...

    def to_prolog_fact(self, relation: CaRelation) -> str:
        ...
