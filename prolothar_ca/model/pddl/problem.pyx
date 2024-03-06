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

cdef class Problem:
    """
    a PDDL problem definition

    https://planning.wiki/ref/pddl/problem
    https://planning.wiki/ref/pddl21/problem
    """

    def __init__(self, problem_name: str, domain: Domain):
        validate.is_not_none(problem_name)
        validate.string.not_empty(problem_name)
        validate.is_not_none(domain)
        self.__problem_name = problem_name
        self.__domain = domain
        self.__objects: dict[str, Object] = {}
        self.__initial_state = InitialState(self)
        self.__goal: list[Condition] = []
        self.__metric: Metric|None = None

    cpdef str get_problem_name(self):
        return self.__problem_name

    def get_domain(self) -> Domain:
        return self.__domain

    def add_object(self, object_name: str, object_type: ObjectType) -> Object:
        validate.is_true(self.__domain.has_type(object_type))
        new_object = Object(object_name, object_type)
        self.__objects[object_name] = new_object
        return new_object

    def get_object_by_name(self, name: str) -> Object:
        return self.__objects[name]

    def get_objects(self) -> list[Object]:
        return list(self.__objects.values())

    def get_objects_of_type(self, object_type: ObjectType) -> list[Object]:
        return [o for o in self.__objects.values() if o.object_type == object_type]

    def get_object_dict(self) -> dict[str, Object]:
        return self.__objects

    def set_initial_state(self, initial_state: InitialState):
        validate.is_not_none(initial_state)
        self.__initial_state = initial_state

    def get_intitial_state(self) -> InitialState:
        return self.__initial_state

    def set_goal(self, condition_list: list[Condition]):
        validate.is_not_none(condition_list)
        self.__goal = condition_list

    def add_goal(self, condition: Condition):
        validate.is_not_none(condition)
        self.__goal.append(condition)

    def get_goal_condition_list(self) -> list[Condition]:
        return self.__goal

    def set_metric(self, metric: Metric):
        self.__metric = metric

    def get_metric(self) -> Metric:
        return self.__metric

    def to_pddl(self) -> str:
        objects_in_pddl = NEWLINE.join(
            f'        {o.name} - {o.object_type.name}'
            for o in sorted(self.__objects.values(), key=lambda x: (x.object_type.name, x.name))
        )

        goal_in_pddl = NEWLINE.join(
            f'        {c.to_pddl().replace("?", "")}'
            for c in self.__goal
        )

        if self.__metric is not None:
            metric_in_pddl = self.__metric.to_pddl(indent='    ') + NEWLINE
        else:
            metric_in_pddl = ''

        return (
            f'(define{NEWLINE}'
            f'    (problem {self.__problem_name}){NEWLINE}'
            f'    (:domain {self.__domain.get_name()}){NEWLINE}'
            f'    (:objects {NEWLINE}'
            f'{objects_in_pddl}{NEWLINE}'
            f'    ){NEWLINE}'
            f'{self.__initial_state.to_pddl(indent="    ")}'
            f'    (:goal (and{NEWLINE}'
            f'{goal_in_pddl}{NEWLINE}'
            f'    )){NEWLINE}'
            f'{metric_in_pddl}'
            f'){NEWLINE}'
        )

    def add_objects_from_parsed_pddl(self, section_content: list[str]):
        if '-' in section_content:
            current_object_names = []
            last_token = None
            token_list = section_content[::-1]
            while token_list:
                token = token_list.pop()
                if last_token == '-':
                    for object_name in current_object_names:
                        self.add_object(object_name, self.__domain.get_type_by_name(token))
                    current_object_names.clear()
                elif token != '-':
                    current_object_names.append(token)
                last_token = token
        else:
            for object_name in section_content:
                self.add_object(object_name, NoType())

    cpdef set_initial_state_from_parsed_pddl(self, list parsed_pddl):
        initial_state = InitialState(self)
        for line in parsed_pddl:
            if line[0] == '=':
                (<set>initial_state.numeric_fluents).add((
                    self.__domain.get_numeric_fluent_by_name(line[1][0]),
                    tuple(map(self.__objects.get, line[1][1:])),
                    int(line[2])
                ))
            else:
                (<set>initial_state.true_predicates).add((
                    self.__domain.get_predicate_by_name(line[0]),
                    tuple(map(self.__objects.get, line[1:]))
                ))
        self.set_initial_state(initial_state)

    def set_metric_from_parsed_pddl(self, parsed_pddl: list):
        if parsed_pddl[0] == 'maximize':
            metric = MaximizeMetric
        elif parsed_pddl[0] == 'minimize':
            metric = MinimizeMetric
        else:
            raise NotImplementedError(parsed_pddl)
        self.set_metric(metric(
            Domain.parse_numeric_fluent_expression(self.__domain, parsed_pddl[1])
        ))

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, Problem) and
            self.__problem_name == (<Problem>other).__problem_name and
            self.__domain == (<Problem>other).__domain and
            self.__objects == (<Problem>other).__objects and
            self.__initial_state.to_pddl() == (<Problem>other).__initial_state.to_pddl() and
            self.__goal == (<Problem>other).__goal and
            self.__metric == (<Problem>other).__metric
        )

    def __repr__(self) -> str:
        return self.to_pddl()

    @staticmethod
    def from_pddl(pddl: str, domain: Domain) -> 'Problem':
        parsed_pddl = nested_expr().parse_string(pddl)[0]
        validate.equals(parsed_pddl[0], 'define')

        validate.equals(parsed_pddl[1][0], 'problem')
        problem = Problem(parsed_pddl[1][1], domain)

        validate.equals(parsed_pddl[2][0], ':domain')
        validate.equals(parsed_pddl[2][1], domain.get_name())

        for pddl_section in parsed_pddl[3:]:
            section_name = pddl_section[0]
            section_content = pddl_section[1:]
            if section_name == ':objects':
                problem.add_objects_from_parsed_pddl(section_content)
            elif section_name == ':init':
                problem.set_initial_state_from_parsed_pddl(section_content)
            elif section_name == ':goal':
                validate.equals(section_content[0][0], 'and')
                problem.set_goal([
                    Domain.parse_condition(domain, raw_condition)
                    for raw_condition in section_content[0][1:]
                ])
            elif section_name == ':metric':
                problem.set_metric_from_parsed_pddl(section_content)
            else:
                raise NotImplementedError(f'unsupported section "{section_name}" with content "{section_content}"')
        return problem
