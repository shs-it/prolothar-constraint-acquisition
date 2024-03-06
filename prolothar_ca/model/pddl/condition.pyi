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

from abc import ABC, abstractmethod

from prolothar_ca.model.pddl.numeric_expression import NumericExpression
from prolothar_ca.model.pddl.object_type import ObjectType
from prolothar_ca.model.pddl.pddl_object import Object


class Condition(ABC):
    @abstractmethod
    def to_pddl(self) -> str: ...
    """
    creates a pddl representation of this condition
    """

    @abstractmethod
    def holds(self, parameter_assignment: dict[str, Object], state, problem) -> bool: ...
    """
    returns True iff the condition holds for the given state and parameter assignment
    """

class PredicateIsTrueCondition(Condition):

    def __init__(self, predicate, parameter_names: list[str]): ...

    def get_predicate(self): ...

    def get_parameter_names(self) -> list[str]: ...

    def to_pddl(self) -> str: ...

    def holds(self, parameter_assignment: dict[str, Object], state, problem) -> bool: ...

class Greater(Condition):

    def __init__(self, expression_a: NumericExpression|int, expression_b: NumericExpression|int): ...

    def to_pddl(self) -> str: ...

    def holds(self, parameter_assignment: dict[str, Object], state, problem) -> bool: ...

    def __eq__(self, other): ...

class GreaterOrEqual(Condition):

    def __init__(self, expression_a: NumericExpression|int, expression_b: NumericExpression|int): ...

    def to_pddl(self) -> str: ...

    def holds(self, parameter_assignment: dict[str, Object], state, problem) -> bool: ...

    def __eq__(self, other): ...

class Less(Condition):

    def __init__(self, expression_a: NumericExpression|int, expression_b: NumericExpression|int): ...

    def to_pddl(self) -> str: ...

    def holds(self, parameter_assignment: dict[str, Object], state, problem) -> bool: ...

class LessOrEqual(Condition):

    def __init__(self, expression_a: NumericExpression|int, expression_b: NumericExpression|int): ...

    def to_pddl(self) -> str: ...

    def holds(self, parameter_assignment: dict[str, Object], state, problem) -> bool: ...

class Equals(Condition):

    def __init__(self, expression_a: NumericExpression|int, expression_b: NumericExpression|int): ...

    def to_pddl(self) -> str: ...

    def holds(self, parameter_assignment: dict[str, Object], state, problem) -> bool: ...

class Not(Condition):

    def __init__(self, condition: Condition): ...

    def to_pddl(self) -> str: ...

    def holds(self, parameter_assignment: dict[str, Object], state, problem) -> bool: ...

class Or(Condition):

    def __init__(self, condition_list: list[Condition]): ...

    def to_pddl(self) -> str: ...

    def holds(self, parameter_assignment: dict[str, Object], state, problem) -> bool: ...

class And(Condition):

    def __init__(self, condition_list: list[Condition]): ...

    def to_pddl(self) -> str: ...

    def holds(self, parameter_assignment: dict[str, Object], state, problem) -> bool: ...

class Exists(Condition):

    def __init__(self, parameter_name: str, parameter_type: ObjectType, condition: Condition): ...

    def to_pddl(self) -> str: ...

    def holds(self, parameter_assignment: dict[str, Object], state, problem) -> bool: ...

class ForAll(Condition):

    def __init__(self, parameter_name: str, parameter_type: ObjectType, condition: Condition): ...

    def to_pddl(self) -> str: ...

    def holds(self, parameter_assignment: dict[str, Object], state, problem) -> bool: ...
