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

from dataclasses import dataclass

from prolothar_ca.model.pddl.action import Action
from prolothar_ca.model.pddl.pddl_object import Object
from prolothar_ca.model.pddl.problem import Problem

@dataclass
class Plan:
    action_list: list[tuple[Action, dict[str, Object]]]
    cost: float

    def is_valid(self, problem: Problem) -> bool:
        current_state = problem.get_intitial_state().to_state()
        for action, parameters in self.action_list:
            if not action.is_applicable(parameters, current_state, problem):
                return False
            current_state = action.apply(parameters, current_state)
        for goal_condition in problem.get_goal_condition_list():
            if not goal_condition.holds(problem.get_object_dict(), current_state, problem):
                return False
        return True