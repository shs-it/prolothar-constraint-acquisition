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

from prolothar_ca.model.pddl.pddl_object import Object
from prolothar_ca.model.pddl.state import State

from prolothar_ca.model.pddl.condition import Condition
from prolothar_ca.model.pddl.effect import Effect
from prolothar_ca.model.pddl.object_type import ObjectType

class Action:
    action_name: str
    parameters: dict[str, ObjectType]
    preconditions: list[Condition]
    effects: list[Effect]

    def __init__(
            self, action_name: str, parameters: dict[str, ObjectType],
            preconditions: list[Condition], effects: list[Effect]): ...

    def to_pddl(self, indent: str = '') -> str: ...

    def is_applicable(self, parameter_assignment: dict[str, Object], state: State, problem) -> bool: ...

    def apply(self, parameter_assignment: dict[str, Object], state: State) -> State: ...
    """
    does not check whether the action is actually applicable!
    """
