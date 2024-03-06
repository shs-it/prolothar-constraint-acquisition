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

from pyparsing import nested_expr

from prolothar_common import validate

from prolothar_ca.model.pddl.utils import NEWLINE
from prolothar_ca.model.pddl.condition import Condition
from prolothar_ca.model.pddl.domain import Domain
from prolothar_ca.model.pddl.initial_state import InitialState
from prolothar_ca.model.pddl.metric import MaximizeMetric, Metric, MinimizeMetric
from prolothar_ca.model.pddl.pddl_object import Object
from prolothar_ca.model.pddl.object_type import NoType, ObjectType

class Problem:
    """
    a PDDL problem definition

    https://planning.wiki/ref/pddl/problem
    https://planning.wiki/ref/pddl21/problem
    """

    def __init__(self, problem_name: str, domain: Domain): ...

    def get_domain(self) -> Domain: ...

    def get_problem_name(self) -> str: ...

    def add_object(self, object_name: str, object_type: ObjectType) -> Object: ...

    def get_object_by_name(self, name: str) -> Object: ...

    def get_objects(self) -> list[Object]: ...

    def get_objects_of_type(self, object_type: ObjectType) -> list[Object]: ...

    def get_object_dict(self) -> dict[str, Object]: ...

    def set_initial_state(self, initial_state: InitialState): ...

    def get_intitial_state(self) -> InitialState: ...

    def set_goal(self, condition_list: list[Condition]): ...

    def add_goal(self, condition: Condition): ...

    def get_goal_condition_list(self) -> list[Condition]: ...

    def set_metric(self, metric: Metric): ...

    def get_metric(self) -> Metric: ...

    def to_pddl(self) -> str: ...

    def add_objects_from_parsed_pddl(self, section_content: list[str]): ...

    def set_initial_state_from_parsed_pddl(self, parsed_pddl: list): ...

    def set_metric_from_parsed_pddl(self, parsed_pddl: list): ...

    @staticmethod
    def from_pddl(pddl: str, domain: Domain) -> 'Problem': ...
