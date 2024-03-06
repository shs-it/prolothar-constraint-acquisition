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

from itertools import chain
from typing import Iterable

from pyparsing import nested_expr
from prolothar_common import validate

from prolothar_ca.model.pddl.utils import NEWLINE
from prolothar_ca.model.pddl.action import Action
from prolothar_ca.model.pddl.condition import And, Condition, Greater, Less, Not, Or, PredicateIsTrueCondition, LessOrEqual, GreaterOrEqual
from prolothar_ca.model.pddl.durative_action import DurativeAction
from prolothar_ca.model.pddl.effect import SetNumericFluent, ForAllEffect, AndEffect, DecreaseEffect, Effect, IncreaseEffect, SetPredicateFalse, SetPredicateTrue, When
from prolothar_ca.model.pddl.numeric_expression import ConstantExpression, NumericExpression, NumericFluentExpression, Add, Divide, Multiply, Subtract
from prolothar_ca.model.pddl.numeric_fluent import NumericFluent
from prolothar_ca.model.pddl.object_type import NoType, ObjectType
from prolothar_ca.model.pddl.predicate import Predicate


class Domain:
    """
    a PDDL domain

    https://planning.wiki/ref/pddl/domain
    https://planning.wiki/ref/pddl21/domain
    """

    def __init__(self, name: str):
        self.__name = name
        self.__requirements: set[str] = set([':typing'])
        self.__object_types: set[ObjectType] = set([NoType()])
        self.__predicates: dict[str, Predicate] = {}
        self.__numeric_fluents: dict[str, NumericFluent] = {}
        self.__actions: dict[str, Action] = {}
        self.__durative_actions: dict[str, DurativeAction] = {}

    def get_name(self) -> str:
        return self.__name

    def add_type(self, type_name: str, parent: str|None = None) -> ObjectType:
        if parent is None or 'None' == parent:
            object_type = ObjectType(type_name)
        else:
            object_type = ObjectType(type_name, parent=self.get_type_by_name(parent))
        self.__object_types.add(object_type)
        return object_type

    def has_type(self, object_type: ObjectType) -> bool:
        return object_type in self.__object_types

    def get_object_types(self) -> set[ObjectType]:
        return self.__object_types

    def get_leaf_object_types(self) -> set[ObjectType]:
        """
        returns all object types that are not parent for another object type
        """
        return self.get_object_types().difference(
            o.parent for o in self.get_object_types() if o.parent is not None)

    def get_type_by_name(self, type_name: str) -> ObjectType:
        for object_type in self.__object_types:
            if object_type.name == type_name:
                return object_type
        raise KeyError(type_name)

    def add_predicate(self, predicate_name: str, parameter_types: list[ObjectType]) -> Predicate:
        self.__check_all_object_types_defined(parameter_types)
        predicate = Predicate(predicate_name, parameter_types)
        self.__predicates[predicate_name] = predicate
        return predicate

    def get_predicate_by_name(self, name: str) -> Predicate:
        try:
            return self.__predicates[name]
        except KeyError as e:
            raise KeyError(f'"{name}" is not a registered predicate in this domain') from e

    def iter_predicates(self) -> Iterable[Predicate]:
        return self.__predicates.values()

    def iter_numeric_fluents(self) -> Iterable[NumericFluent]:
        return self.__numeric_fluents.values()

    def add_numeric_fluent(self, variable_name: str, parameter_types: list[ObjectType]) -> NumericFluent:
        self.__check_all_object_types_defined(parameter_types)
        self.__requirements.add(':fluents')
        numeric_fluent = NumericFluent(variable_name, parameter_types)
        self.__numeric_fluents[variable_name] = numeric_fluent
        return numeric_fluent

    def get_numeric_fluent_by_name(self, name: str) -> NumericFluent:
        try:
            return self.__numeric_fluents[name]
        except KeyError as e:
            raise KeyError(f'"{name}" is not a registered numeric fluent in this domain') from e

    def add_action(
            self, action_name: str, parameters: dict[str, ObjectType],
            preconditions: list[Condition], effects: list[Effect]):
        self.__check_all_object_types_defined(parameters.values())
        self.__check_negative_preconditions(preconditions)
        self.__actions[action_name] = Action(
            action_name, parameters, preconditions, effects)

    def get_action_by_name(self, name: str) -> Action:
        return self.__actions[name]

    def iterable_actions(self) -> Iterable[Action]:
        return self.__actions.values()

    def add_durative_action(
            self,
            action_name: str,
            parameters: dict[str, ObjectType],
            duration: int|NumericExpression,
            start_conditions: list[Condition],
            overall_conditions: list[Condition],
            start_effects: list[Effect],
            end_effects: list[Effect]):
        self.__check_all_object_types_defined(parameters.values())
        self.__check_negative_preconditions(chain(start_conditions, overall_conditions))
        self.__requirements.add(':durative-actions')
        self.__durative_actions[action_name] = DurativeAction(
            action_name, parameters, duration,
            start_conditions, overall_conditions,
            start_effects, end_effects)

    def __check_negative_preconditions(self, preconditions: Iterable[Condition]):
        if any(isinstance(c, Not) for c in preconditions):
            self.__requirements.add(':negative-preconditions')

    def __check_all_object_types_defined(self, object_types: Iterable[ObjectType]):
        for parameter_typ in object_types:
            if parameter_typ not in self.__object_types:
                raise ValueError(f'unknown object type "{parameter_typ}" not in "{self.__object_types}"')

    def to_pddl(self) -> str:
        if self.__numeric_fluents:
            functions = (
                f'    (:functions{NEWLINE}'
                f'        {(NEWLINE + "        ").join(p.to_pddl() for p in self.__numeric_fluents.values())}{NEWLINE}'
                f'    ){NEWLINE}'
            )
        else:
            functions = ''
        return (
            f'(define{NEWLINE}'
            f'    (domain {self.__name}){NEWLINE}'
            f'    (:requirements {" ".join(sorted(self.__requirements))}){NEWLINE}'
            f'    (:types {" ".join(sorted(t.name for t in self.__object_types))}){NEWLINE}'
            f'    (:predicates{NEWLINE}'
            f'        {(NEWLINE + "        ").join(p.to_pddl() for p in self.__predicates.values())}{NEWLINE}'
            f'    ){NEWLINE}'
            f'{functions}'
            f'{NEWLINE.join(action.to_pddl(indent="    ") for action in self.__actions.values())}{NEWLINE}'
            f'{NEWLINE.join(action.to_pddl(indent="    ") for action in self.__durative_actions.values())}{NEWLINE}'
            ')'
        )

    def __eq__(self, other):
        if not isinstance(other, Domain):
            return False
        return (
            self.__name == other.__name and
            self.__actions == other.__actions and
            self.__durative_actions == other.__durative_actions and
            self.__numeric_fluents == other.__numeric_fluents and
            self.__predicates == other.__predicates and
            self.__object_types == other.__object_types and
            self.__requirements == other.__requirements
        )

    def __repr__(self):
        return self.to_pddl()

    @staticmethod
    def from_pddl(pddl: str) -> 'Domain':
        parsed_pddl = nested_expr().parse_string(pddl)[0]
        validate.equals(parsed_pddl[0], 'define')

        validate.equals(parsed_pddl[1][0], 'domain')
        domain = Domain(parsed_pddl[1][1])

        for pddl_section in parsed_pddl[2:]:
            section_name = pddl_section[0]
            section_content = pddl_section[1:]
            if section_name == ':requirements':
                validate.collection.is_subset(
                    [requirement.strip(',') for requirement in section_content],
                    [':strips', ':durative-actions', ':fluents', ':typing', ':negative-preconditions'])
            elif section_name == ':types':
                domain.parse_types(section_content)
            elif section_name == ':predicates':
                for predicate in section_content:
                    domain.add_predicate(*Domain.parse_predicate(predicate, domain))
            elif section_name == ':functions':
                for numeric_fluent in section_content:
                    domain.add_numeric_fluent(*Domain.parse_predicate(numeric_fluent, domain))
            elif section_name == ':action':
                Domain.parse_and_add_action(domain, section_content)
            elif section_name == ':durative-action':
                Domain.parse_and_add_durative_action(domain, section_content)
            else:
                raise NotImplementedError(f'unsupported section "{section_name}" with content "{section_content}"')
        return domain

    def parse_types(self, section_content: list[str]):
        if '-' in section_content:
            section_content = ' '.join(section_content).split(' - ')
            for i in range(len(section_content) - 1):
                parent_type_name = section_content[i+1].split()[0]
                if i == 0:
                    for type_name in section_content[i].split():
                        self.add_type(type_name, parent=parent_type_name)
                else:
                    for type_name in section_content[i].split()[1:]:
                        self.add_type(type_name, parent=parent_type_name)
        else:
            for type_name in section_content:
                self.add_type(type_name)

    @staticmethod
    def parse_predicate(predicate: list[str], domain: 'Domain') -> tuple[str, list[ObjectType]]:
        parameters = []
        #with typing
        if len(predicate) % 3 == 1:
            # format is "name, parameter_name_1, -, parameter_type_1, ..."
            i = 3
            while i < len(predicate):
                parameters.append(domain.get_type_by_name(predicate[i]))
                i += 3
        #without typing
        else:
            for _ in predicate[1:]:
                parameters.append(NoType())

        return predicate[0], parameters

    @staticmethod
    def parse_and_add_action(domain: 'Domain', action: list):
        validate.equals(action[1], ':parameters')
        validate.equals(action[3], ':precondition')
        validate.equals(action[4][0], 'and')

        validate.equals(action[5], ':effect')
        validate.equals(action[6][0], 'and')

        domain.add_action(
            action[0],
            Domain.parse_action_parameters(action[2], domain),
            [
                Domain.parse_condition(domain, condition)
                for condition in action[4][1:]
            ],
            [
                Domain.parse_effect(domain, effect)
                for effect in action[6][1:]
            ]
        )

    @staticmethod
    def parse_action_parameters(parameters: list, domain: 'Domain') -> dict[str, ObjectType]:
        #for some unknown reason, '-' in parameters evaluates to False
        if len(parameters) > 1 and parameters[1] == '-':
            return {
                parameters[i].lstrip('?'): domain.get_type_by_name(parameters[i+2])
                for i in range(0, len(parameters), 3)
            }
        else:
            return {
                p.lstrip('?'): NoType()
                for p in parameters
            }

    @staticmethod
    def parse_and_add_durative_action(domain: 'Domain', durative_action: list):
        validate.equals(durative_action[1], ':parameters')
        validate.equals(durative_action[3], ':duration')
        validate.equals(durative_action[5], ':condition')
        validate.equals(durative_action[6][0], 'and')
        start_conditions = []
        overall_conditions = []
        for condition in durative_action[6][1:]:
            parsed_condition = Domain.parse_condition(domain, condition[2])
            if condition[0] == 'at' and condition[1] == 'start':
                start_conditions.append(parsed_condition)
            elif condition[0] == 'over' and condition[1] == 'all':
                overall_conditions.append(parsed_condition)

        validate.equals(durative_action[7], ':effect')
        validate.equals(durative_action[8][0], 'and')
        start_effects = []
        end_effects = []
        for effect in durative_action[8][1:]:
            parsed_effect = Domain.parse_effect(domain, effect[2])
            if effect[0] == 'at' and effect[1] == 'start':
                start_effects.append(parsed_effect)
            elif effect[0] == 'at' and effect[1] == 'end':
                end_effects.append(parsed_effect)
            else:
                raise NotImplementedError(effect)

        domain.add_durative_action(
            durative_action[0],
            {
                durative_action[2][i][1:]: ObjectType(durative_action[2][i+2])
                for i in range(0, len(durative_action[2]), 3)
            },
            Domain.parse_numeric_fluent_expression(domain, durative_action[4][2]),
            start_conditions,
            overall_conditions,
            start_effects,
            end_effects
        )

    @staticmethod
    def parse_condition(domain: 'Domain', condition: list):
        if condition[0] == '>':
            return Greater(
                Domain.parse_numeric_fluent_expression(domain, condition[1]),
                Domain.parse_numeric_fluent_expression(domain, condition[2]),
            )
        elif condition[0] == '<':
            return Less(
                Domain.parse_numeric_fluent_expression(domain, condition[1]),
                Domain.parse_numeric_fluent_expression(domain, condition[2]),
            )
        elif condition[0] == '>=':
            return GreaterOrEqual(
                Domain.parse_numeric_fluent_expression(domain, condition[1]),
                Domain.parse_numeric_fluent_expression(domain, condition[2]),
            )
        elif condition[0] == '<=':
            return LessOrEqual(
                Domain.parse_numeric_fluent_expression(domain, condition[1]),
                Domain.parse_numeric_fluent_expression(domain, condition[2]),
            )
        elif condition[0] == 'not':
            return Not(Domain.parse_condition(domain, condition[1]))
        elif condition[0] == 'and':
            return And([
                Domain.parse_condition(domain, term)
                for term in condition[1:]
            ])
        elif condition[0] == 'or':
            return Or([
                Domain.parse_condition(domain, term)
                for term in condition[1:]
            ])
        else:
            return PredicateIsTrueCondition(
                domain.get_predicate_by_name(condition[0]),
                [
                    p.lstrip('?') for p in condition[1:]
                ]
            )

    @staticmethod
    def parse_effect(domain: 'Domain', effect: list):
        if effect[0] == 'decrease':
            return DecreaseEffect(
                domain.get_numeric_fluent_by_name(effect[1][0]),
                [p.lstrip('?') for p in effect[1][1:]],
                Domain.parse_numeric_fluent_expression(domain, effect[2])
            )
        elif effect[0] == 'increase':
            return IncreaseEffect(
                domain.get_numeric_fluent_by_name(effect[1][0]),
                [p.lstrip('?') for p in effect[1][1:]],
                Domain.parse_numeric_fluent_expression(domain, effect[2])
            )
        elif effect[0] == 'not':
            return SetPredicateFalse(
                domain.get_predicate_by_name(effect[1][0]),
                [
                    p.lstrip('?') for p in effect[1][1:]
                ]
            )
        elif effect[0] == 'and':
            return AndEffect([
                Domain.parse_effect(domain, e) for e in effect[1:]
            ])
        elif effect[0] == 'when':
            return When(
                Domain.parse_condition(domain, effect[1]),
                Domain.parse_effect(domain, effect[2])
            )
        elif effect[0] == 'forall' and len(effect) == 3:
            return ForAllEffect(
                effect[1][0].lstrip('?'),
                domain.get_type_by_name(effect[1][2]),
                Domain.parse_effect(domain, effect[2])
            )
        elif effect[0] == 'assign' and len(effect) == 3:
            return SetNumericFluent(
                domain.get_numeric_fluent_by_name(effect[1][0]),
                [
                    p.lstrip('?') for p in effect[1][1:]
                ],
                Domain.parse_numeric_fluent_expression(domain, effect[2])
            )
        else:
            return SetPredicateTrue(
                domain.get_predicate_by_name(effect[0]),
                [
                    p.lstrip('?') for p in effect[1:]
                ]
            )

    @staticmethod
    def parse_numeric_fluent_expression(domain: 'Domain', numeric_fluent_expression: list|str):
        if isinstance(numeric_fluent_expression, str):
            return ConstantExpression(int(numeric_fluent_expression))
        elif len(numeric_fluent_expression) == 1:
            try:
                return ConstantExpression(int(numeric_fluent_expression[0]))
            except ValueError:
                return NumericFluentExpression(
                    domain.get_numeric_fluent_by_name(numeric_fluent_expression[0]),
                    []
                )
        elif len(numeric_fluent_expression) == 2:
            return NumericFluentExpression(
                domain.get_numeric_fluent_by_name(numeric_fluent_expression[0]),
                [p.lstrip('?') for p in numeric_fluent_expression[1:]]
            )
        elif len(numeric_fluent_expression) == 3:
            return {
                '+': Add,
                '-': Subtract,
                '*': Multiply,
                '/': Divide
            }[numeric_fluent_expression[0]](
                Domain.parse_numeric_fluent_expression(domain, numeric_fluent_expression[1]),
                Domain.parse_numeric_fluent_expression(domain, numeric_fluent_expression[2])
            )
        else:
            raise NotImplementedError(numeric_fluent_expression)