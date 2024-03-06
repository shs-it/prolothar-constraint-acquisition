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

from random import Random
from itertools import groupby, product
from functools import reduce
import gc
from tqdm import trange, tqdm
from prolothar_common import validate
from prolothar_common.collections.list_utils import shuffle_together

from prolothar_ca.ca.dataset_generator.dataset_generator import CaDatasetGenerator

from prolothar_ca.model.ca.dataset import CaDataset
from prolothar_ca.model.ca.example import CaExample
from prolothar_ca.model.ca.targets import RelationTarget
from prolothar_ca.model.ca.obj import CaObjectType, CaObject
from prolothar_ca.model.ca.variable_type import CaBoolean, CaNumber, CaVariableType
from prolothar_ca.model.ca.relation import CaRelationType, CaRelation
from prolothar_ca.model.ca.constraints.conjunction import And
from prolothar_ca.model.ca.constraints.constraint import CaConstraint
from prolothar_ca.model.ca.constraints.boolean import RelationIsFalse, Not
from prolothar_ca.model.ca.constraints.boolean import RelationIsTrue
from prolothar_ca.model.ca.constraints.boolean import BooleanFeatureIsTrue
from prolothar_ca.model.ca.constraints.quantifier import ForAll
from prolothar_ca.model.ca.constraints.query import Filter, Product, AllOfType

from prolothar_ca.model.pddl.domain import Domain
from prolothar_ca.model.pddl.problem import Problem
from prolothar_ca.model.pddl.plan import Plan
from prolothar_ca.model.pddl.action import Action
from prolothar_ca.model.pddl.condition import PredicateIsTrueCondition
from prolothar_ca.model.pddl.object_type import ObjectType
from prolothar_ca.model.pddl.pddl_object import Object
from prolothar_ca.model.pddl.state import State

IS_VALID_ACTION = 'is_valid_action'

class PddlCaDatasetGenerator(CaDatasetGenerator):

    def __init__(
            self, domain: Domain, problem_list: list[Problem], plan_list: list[Plan],
            action_of_interest: Action, search_new_valid_actions: bool = False,
            filter_actions_with_duplicate_parameter: bool = False,
            relations_to_ignore: set[str]|list[str]|None = None,
            nr_of_target_relation_samples: int|None = None,
            nr_of_feature_relation_samples: int|None = None,
            ignore_parameters: list[str]|None = None,
            remove_unused_objects: bool = False):
        if relations_to_ignore is not None:
            validate.is_in(type(relations_to_ignore), [set, list, tuple])
            self.__relations_to_ignore = relations_to_ignore
        else:
            self.__relations_to_ignore = set()
        if ignore_parameters is not None:
            validate.is_in(type(ignore_parameters), [set, list, tuple])
            self.__ignore_parameters = ignore_parameters
        else:
            self.__ignore_parameters = []
        self.domain = domain
        self.plan_list = plan_list
        self.problem_list = problem_list
        self.action_of_interest = action_of_interest
        self.__filter_actions_with_duplicate_parameter = filter_actions_with_duplicate_parameter
        self.__relation_name_to_pddl_name = {}
        self.__empty_dataset = CaDataset(
            self.__pddl_to_ca_types_definition(self.domain),
            self.__pddl_to_ca_relations_definition(self.domain, self.action_of_interest)
        )
        self.__current_plan_index = 0
        self.__next_positive_examples = []
        self.__search_new_valid_actions = search_new_valid_actions
        self.__nr_of_target_relation_samples = nr_of_target_relation_samples
        self.__nr_of_feature_relation_samples = nr_of_feature_relation_samples
        self.__remove_unused_objects = remove_unused_objects

    def __pddl_to_ca_types_definition(self, domain: Domain) -> dict[str, CaObjectType]:
        return {
            object_type.name: CaObjectType(
                object_type.name, self.__create_ca_feature_definition(object_type, domain))
            for object_type in domain.get_leaf_object_types()
        }

    def __create_ca_feature_definition(self, object_type: ObjectType|None, domain: Domain) -> dict[str, CaVariableType]:
        if object_type is None:
            return {}
        else:
            return {
                predicate.name: CaBoolean()
                for predicate in domain.iter_predicates()
                if len(predicate.parameter_types) == 1
                and object_type.is_of_type(predicate.parameter_types[0]) \
                and predicate.name not in self.__relations_to_ignore
            } | {
                fluent.name: CaNumber()
                for fluent in domain.iter_numeric_fluents()
                if len(fluent.parameter_types) == 1
                and object_type.is_of_type(fluent.parameter_types[0]) \
                and fluent.name not in self.__relations_to_ignore
            } | self.__create_ca_feature_definition(object_type.parent, domain)

    def __pddl_to_ca_relations_definition(
            self, domain: Domain, action_of_interest: Action) -> dict[str, CaObjectType]:
        leaf_object_types = domain.get_leaf_object_types()
        relations_definition = {}
        for predicate in domain.iter_predicates():
            if len(predicate.parameter_types) != 1 and predicate.name not in self.__relations_to_ignore:
                relations_definition.update(self.__resolve_relation_types(
                    predicate.name, predicate.parameter_types, CaBoolean(), leaf_object_types))
        for fluent in domain.iter_numeric_fluents():
            if len(fluent.parameter_types) != 1 and fluent.name not in self.__relations_to_ignore:
                relations_definition.update(self.__resolve_relation_types(
                    fluent.name, fluent.parameter_types, CaNumber(), leaf_object_types))
        for parameter_name, parameter_type in action_of_interest.parameters.items():
            if parameter_type not in leaf_object_types:
                raise NotImplementedError(
                    'we currently do not support inheritance for action parameter types. '
                    f'[{", ".join(o.name for o in leaf_object_types)}] are supported leaf object types, '
                    f'but parameter "{parameter_name}" is of non-leaf type {parameter_type.name}'
                )
        relations_definition[IS_VALID_ACTION] = CaRelationType(
            IS_VALID_ACTION,
            tuple(
                p.name for t,p in sorted(action_of_interest.parameters.items())
                if t not in self.__ignore_parameters
            ),
            CaBoolean()
        )
        return relations_definition

    def __resolve_relation_types(
            self, base_relation_name: str, parameter_types: list[ObjectType],
            relation_type: CaVariableType, leaf_object_types: set[ObjectType],
            recursive_call: bool = False) -> dict[str, CaRelationType]:
        if all(t in leaf_object_types for t in parameter_types):
            if recursive_call:
                resolved_relation_name = self.__create_resolved_relation_name(
                    base_relation_name, parameter_types)
            else:
                resolved_relation_name = base_relation_name
            self.__relation_name_to_pddl_name[resolved_relation_name] = base_relation_name
            return {
                resolved_relation_name: CaRelationType(
                    resolved_relation_name, tuple(t.name for t in parameter_types), relation_type)
            }
        else:
            relation_types = {}
            for resolved_parameter_types in product(*[self.__resolve_object_type(t, leaf_object_types) for t in parameter_types]):
                relation_types.update(self.__resolve_relation_types(
                    base_relation_name, resolved_parameter_types, relation_type, leaf_object_types, recursive_call=True))
            return relation_types

    def __resolve_object_type(self, object_type: ObjectType, leaf_object_types: set[ObjectType]) -> list[ObjectType]:
        return [
            leaf_object_type for leaf_object_type in leaf_object_types
            if leaf_object_type.is_of_type(object_type)
        ]

    def __create_resolved_relation_name(self, base_relation_name: str, resolved_parameter_types: tuple[ObjectType]) -> str:
        if len(resolved_parameter_types) == 2:
            return f'{resolved_parameter_types[0].name}_{base_relation_name}_{resolved_parameter_types[1].name}'
        else:
            return f'{base_relation_name}_{"_".join(t.name for t in resolved_parameter_types)}'

    def _create_empty_dataset(self) -> CaDataset:
        return self.__empty_dataset.empty_copy()

    def generate(
            self, nr_of_positive_examples: int,
            nr_of_negative_examples: int,
            random_seed: int|None = None) -> CaDataset:
        nr_of_available_examples = 0
        for plan in self.plan_list:
            for action,_ in plan.action_list:
                if action == self.action_of_interest:
                    nr_of_available_examples += 1
        if not self.__search_new_valid_actions:
            validate.less_or_equal(
                nr_of_positive_examples, nr_of_available_examples,
                msg=f'There are only {nr_of_available_examples} positive examples available '
                f'but {nr_of_positive_examples} are demanded'
            )
        self.plan_list, self.problem_list = shuffle_together(
            self.plan_list, self.problem_list, random=Random(random_seed))
        self.__current_plan_index = 0
        random_generator = Random(random_seed)
        dataset = self._create_empty_dataset()
        gc.disable()
        for _ in trange(nr_of_positive_examples, desc='generate positive examples', leave=False):
            dataset.add_example(
                self._generate_positive_example(random_generator),
                validate=self.__nr_of_target_relation_samples is None
            )
        for _ in trange(nr_of_negative_examples, desc='generate negative examples', leave=False):
            dataset.add_example(
                self._generate_negative_example(random_generator),
                validate=self.__nr_of_target_relation_samples is None
            )
        gc.enable()
        if self.__remove_unused_objects:
            self.__remove_unused_objects_from_dataset(dataset)
        return dataset

    def _generate_positive_example(self, random_generator: Random) -> CaExample:
        if not self.__next_positive_examples:
            try:
                plan = self.plan_list[self.__current_plan_index]
                problem = self.problem_list[self.__current_plan_index]
                validate.is_true(plan.is_valid(problem))
                self.__next_positive_examples = []
                current_state = problem.get_intitial_state().to_state()
                for action, parameters in plan.action_list:
                    if action == self.action_of_interest and (\
                    not self.__filter_actions_with_duplicate_parameter \
                    or len(parameters.values()) == len(set(parameters.values()))):
                        validate.is_true(self.action_of_interest.is_applicable(parameters, current_state, problem))
                        self.__next_positive_examples.append(
                            self.__plan_step_to_ca_example(parameters, current_state, problem, random_generator, True))
                    current_state = action.apply(parameters, current_state)
            except IndexError:
                if not self.__search_new_valid_actions or self.__current_plan_index >= 2 * len(self.plan_list):
                    raise ValueError('No further positive example available')
                plan = self.plan_list[self.__current_plan_index - len(self.plan_list)]
                problem = self.problem_list[self.__current_plan_index - len(self.problem_list)]
                current_state = problem.get_intitial_state().to_state()
                for action, parameters in plan.action_list:
                    if action == self.action_of_interest:
                        for parameter_combination in self.__yield_all_possible_action_of_interest_parameters(problem):
                            if (not self.__filter_actions_with_duplicate_parameter \
                            or len(parameter_combination.values()) == len(set(parameter_combination.values()))) \
                            and self.action_of_interest.is_applicable(parameter_combination, current_state, problem):
                                self.__next_positive_examples.append(
                                    self.__plan_step_to_ca_example(parameter_combination, current_state, problem, random_generator, True))
                    current_state = action.apply(parameters, current_state)
            self.__current_plan_index += 1
        #might be that the current plan did not contain any positive examples => go to the next one and try again
        if not self.__next_positive_examples:
            return self._generate_positive_example(random_generator)
        return self.__next_positive_examples.pop()

    def __yield_all_possible_action_of_interest_parameters(self, problem: Problem):
        parameter_name_list, parameter_type_list = zip(*self.action_of_interest.parameters.items())
        parameter_object_sets = [problem.get_objects_of_type(t) for t in parameter_type_list]
        for parameter_value_tuple in product(*parameter_object_sets):
            yield {
                parameter_name: parameter_value
                for parameter_name, parameter_value in zip(parameter_name_list, parameter_value_tuple)
            }

    def __plan_step_to_ca_example(
            self, action_parameters: dict[str, Object], current_state: State,
            problem: Problem, random_generator: Random, is_valid_solution: bool):
        for parameter_name in self.__ignore_parameters:
            action_parameters.pop(parameter_name)
        all_objects_per_type = {
            object_type: set(self.__pddl_object_to_ca_object(o, problem, current_state) for o in object_list)
            for object_type, object_list in
            groupby(sorted(problem.get_objects(), key= lambda o: o.object_type.name), key= lambda o: o.object_type.name)
            if self.__empty_dataset.has_object_type(object_type)
        }
        example = CaExample(
            all_objects_per_type,
            {},
            is_valid_solution,
        )
        for relation_type in self.__empty_dataset.get_relation_types():
            if relation_type.name != IS_VALID_ACTION and relation_type.name not in self.__relations_to_ignore:
                self.__add_ca_relations_from_pddl(example, relation_type, problem, current_state, random_generator)
        self.__add_is_valid_action_ca_relations_from_pddl(example, action_parameters, random_generator)
        return example

    def __add_is_valid_action_ca_relations_from_pddl(
            self, example: CaExample, action_parameters: dict[str, Object], random_generator: Random):
        relation_type = self.__empty_dataset.get_relation_type(IS_VALID_ACTION)
        action_parameters_tuple = tuple(
            example.get_object_by_type_and_id(parameter_value.object_type.name, parameter_value.name)
            for _, parameter_value in sorted(
                action_parameters.items(), key=lambda x: (x[1].object_type.name, x[0])
            )
        )
        if self.__nr_of_target_relation_samples is None:
            for parameter_objects in product(*[
                    example.all_objects_per_type[p] for p
                    in relation_type.parameter_types]):
                relation_parameter_tuple = tuple(
                    example.get_object_by_type_and_id(parameter_type, parameter.object_id)
                    for parameter, parameter_type in zip(parameter_objects, relation_type.parameter_types)
                )
                example.add_relation(CaRelation(
                    relation_type.name,
                    relation_parameter_tuple,
                    action_parameters_tuple == relation_parameter_tuple
                ))
        else:
            example.add_relation(CaRelation(
                relation_type.name,
                action_parameters_tuple,
                True
            ))
            i = 0
            objects_per_parameter = [
                list(example.all_objects_per_type[p])
                for p in relation_type.parameter_types
            ]
            while i < self.__nr_of_target_relation_samples:
                parameter_objects = [
                    random_generator.choice(x) for x in objects_per_parameter
                ]
                relation_parameter_tuple = tuple(
                    example.get_object_by_type_and_id(parameter_type, parameter.object_id)
                    for parameter, parameter_type in zip(parameter_objects, relation_type.parameter_types)
                )
                example.add_relation(CaRelation(
                    relation_type.name,
                    relation_parameter_tuple,
                    action_parameters_tuple == relation_parameter_tuple
                ))
                i += 1

    def __add_ca_relations_from_pddl(
            self, example: CaExample, relation_type: CaRelationType,
            problem: Problem, current_state: State, random_generator: Random):
        nr_of_feature_relations = reduce(lambda a,b: a*b, (len(example.all_objects_per_type[p]) for p in relation_type.parameter_types), 1)
        if self.__nr_of_feature_relation_samples is None or nr_of_feature_relations < self.__nr_of_feature_relation_samples:
            for parameter_objects in product(*[example.all_objects_per_type[p] for p in relation_type.parameter_types]):
                relation_parameter_tuple = tuple(
                    example.get_object_by_type_and_id(parameter_type, parameter.object_id)
                    for parameter, parameter_type in zip(parameter_objects, relation_type.parameter_types)
                )
                example.add_relation(CaRelation(
                    relation_type.name,
                    relation_parameter_tuple,
                    relation_type.value_type.get_relation_value_from_pddl_state(
                        problem, current_state, self.__relation_name_to_pddl_name[relation_type.name],
                        tuple(problem.get_object_by_name(r.object_id) for r in relation_parameter_tuple)
                    )
                ))
        else:
            i = 0
            objects_per_parameter = [
                list(example.all_objects_per_type[p])
                for p in relation_type.parameter_types
            ]
            while i < self.__nr_of_feature_relation_samples:
                parameter_objects = [
                    random_generator.choice(x) for x in objects_per_parameter
                ]
                relation_parameter_tuple = tuple(
                    example.get_object_by_type_and_id(parameter_type, parameter.object_id)
                    for parameter, parameter_type in zip(parameter_objects, relation_type.parameter_types)
                )
                example.add_relation(CaRelation(
                    relation_type.name,
                    relation_parameter_tuple,
                    relation_type.value_type.get_relation_value_from_pddl_state(
                        problem, current_state, self.__relation_name_to_pddl_name[relation_type.name],
                        tuple(problem.get_object_by_name(r.object_id) for r in relation_parameter_tuple)
                    )
                ))
                i += 1

    def __pddl_object_to_ca_object(self, pddl_object: Object, problem: Problem, current_state: State) -> CaObject:
        features = {}
        ca_object_type = self.__empty_dataset.get_object_type(pddl_object.object_type.name)
        for feature_name, feature_type in ca_object_type.feature_definition.items():
            features[feature_name] = feature_type.get_feature_value_from_pddl_state(
                problem, current_state, pddl_object, feature_name)
        return CaObject(pddl_object.name, pddl_object.object_type.name, features)

    def _generate_negative_example(self, random_generator: Random) -> CaExample:
        problem_index = random_generator.randrange(len(self.problem_list))
        problem = self.problem_list[problem_index]
        plan = self.plan_list[problem_index]
        state_index = random_generator.randrange(len(plan.action_list))
        current_state = problem.get_intitial_state().to_state()
        for i in range(state_index):
            action, parameters = plan.action_list[i]
            validate.is_true(action.is_applicable(parameters, current_state, problem))
            current_state = action.apply(parameters, current_state)
        parameters = {}
        while True:
            for parameter_name, parameter_type in self.action_of_interest.parameters.items():
                parameters[parameter_name] = random_generator.choice(problem.get_objects_of_type(parameter_type))
            if not self.action_of_interest.is_applicable(parameters, current_state, problem):
                break
        return self.__plan_step_to_ca_example(parameters, current_state, problem, random_generator, False)

    def get_ground_truth_constraints(self) -> list[CaConstraint]:
        relation_type = self.__empty_dataset.get_relation_type(IS_VALID_ACTION)
        variable_names = tuple(sorted(self.action_of_interest.parameters.keys()))
        return [ForAll(
            Filter(
                Product([
                    AllOfType(parameter_type, variable)
                    for parameter_type, variable in zip(
                        relation_type.parameter_types,
                        variable_names
                    )
                ]),
                self.__create_ca_filter_constraint()
            ),
            RelationIsFalse(relation_type, variable_names)
        )]

    def __create_ca_filter_constraint(self):
        if len(self.action_of_interest.preconditions) > 1:
            return Not(And([
                self.__pddl_to_ca_filter_constraint(condition)
                for condition in self.action_of_interest.preconditions
            ]))
        else:
            raise NotImplementedError(self.preconditions)

    def __pddl_to_ca_filter_constraint(self, condition):
        if isinstance(condition, PredicateIsTrueCondition):
            if len(condition.get_predicate().parameter_types) == 1:
                return BooleanFeatureIsTrue(
                    condition.get_predicate().parameter_types[0].name,
                    condition.get_parameter_names()[0],
                    condition.get_predicate().name
                )
            else:
                return RelationIsTrue(
                    self.__empty_dataset.get_relation_type(condition.get_predicate().name),
                    tuple(condition.get_parameter_names())
                )
        else:
            raise NotImplementedError((type(condition), condition))

    def get_target(self) -> RelationTarget:
        return RelationTarget(IS_VALID_ACTION)

    def __remove_unused_objects_from_dataset(self, dataset: CaDataset):
        print('remove all unused objects from dataset')
        used_objects = set()
        for example in tqdm(dataset, total=len(dataset), desc='collect objects'):
            for relation in example.relations[IS_VALID_ACTION]:
                if relation.value:
                    used_objects.update(relation.objects)
        print(f'keep objects of type {set(o.type_name for o in used_objects)}')
        for example in tqdm(dataset, total=len(dataset), desc='remove objects'):
            example.remove_all_objects_not_in_set(used_objects)
        print(
            f'removed all unused objects from dataset. {len(used_objects)} left. '
            f'{len(used_objects)}^2 = {len(used_objects)**2}'
        )