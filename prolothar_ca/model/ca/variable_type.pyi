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

from prolothar_ca.model.pddl.problem import Problem
from prolothar_ca.model.pddl.state import State
from prolothar_ca.model.pddl.pddl_object import Object

class CaBoolean:
    def to_prolog_example(self, relation_name: str, relation_objects: list, relation_value: bool): ...

    def to_prolog_fact(self, relation_name: str, relation_objects: list, relation_value: bool): ...

    def get_value_arity(self) -> int: ...

    def get_sqlite_type_name(self) -> str: ...

    def format_value_sqlite(self, value: bool) -> str: ...

    def get_feature_value_from_pddl_state(
            self, problem: Problem, current_state: State, pddl_object: Object,
            feature_name: str) -> bool: ...

    def get_relation_value_from_pddl_state(
            self, problem: Problem, current_state: State, relation_name: str,
            relation_parameters: tuple[Object]) -> bool: ...

class CaNumber:
    def to_prolog_example(self, relation_name: str, relation_objects: list, relation_value: float|int): ...

    def to_prolog_fact(self, relation_name: str, relation_objects: list, relation_value: float|int): ...

    def get_value_arity(self) -> int: ...

    def get_sqlite_type_name(self) -> str: ...

    def format_value_sqlite(self, value: float) -> str: ...

    def get_feature_value_from_pddl_state(
            self, problem: Problem, current_state: State, pddl_object: Object,
            feature_name: str) -> int|float: ...

    def get_relation_value_from_pddl_state(
            self, problem: Problem, current_state: State, relation_name: str,
            relation_parameters: tuple[Object]) -> bool: ...

CaVariableType = CaBoolean | CaNumber