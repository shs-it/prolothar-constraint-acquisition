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
from prolothar_ca.model.pddl.condition import Condition
from prolothar_ca.model.pddl.numeric_expression import NumericExpression
from prolothar_ca.model.pddl.object_type import ObjectType
from prolothar_ca.model.pddl.pddl_object import Object


class Effect(ABC):
    @abstractmethod
    def to_pddl(self) -> str: ...
    """
    creates a pddl representation of this effect
    """

    @abstractmethod
    def modify_state(self, parameter_assignment: dict[str, Object], state): ...
    """
    executes the effect by modifying the given state
    """

class SetPredicateTrue(Effect):

    def __init__(self, predicate, parameter_names: list[str]): ...

    def to_pddl(self) -> str: ...

    def modify_state(self, parameter_assignment: dict[str, Object], state): ...

    def get_parameter_names(self) -> list[str]: ...

class SetPredicateFalse(Effect):

    def __init__(self, predicate, parameter_names: list[str]): ...

    def to_pddl(self) -> str: ...

    def modify_state(self, parameter_assignment: dict[str, Object], state): ...

    def get_parameter_names(self) -> list[str]: ...

class DecreaseEffect(Effect):

    def __init__(self, numeric_fluent, parameter_names: list[str], value: NumericExpression|int): ...

    def to_pddl(self) -> str: ...

    def modify_state(self, parameter_assignment: dict[str, Object], state): ...

class IncreaseEffect(Effect):

    def __init__(self, numeric_fluent, parameter_names: list[str], value: NumericExpression|int): ...

    def to_pddl(self) -> str: ...

    def modify_state(self, parameter_assignment: dict[str, Object], state): ...

class SetNumericFluent(Effect):

    def __init__(self, numeric_fluent, parameter_names: list[str], value: NumericExpression|int): ...

    def to_pddl(self) -> str: ...

    def modify_state(self, parameter_assignment: dict[str, Object], state): ...

class ForAllEffect(Effect):

    def __init__(self, parameter_name: str, parameter_type: ObjectType, effect: Effect): ...

    def to_pddl(self) -> str: ...

    def modify_state(self, parameter_assignment: dict[str, Object], state): ...

class When(Effect):

    def __init__(self, condition: Condition, effect: Effect): ...

    def to_pddl(self) -> str: ...

    def modify_state(self, parameter_assignment: dict[str, Object], state): ...

class AndEffect(Effect):

    def __init__(self, effect_list: list[Effect]): ...

    def to_pddl(self) -> str: ...

    def modify_state(self, parameter_assignment: dict[str, Object], state): ...
