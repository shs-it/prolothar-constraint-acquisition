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

from functools import reduce
from typing import Generator
from more_itertools import powerset
import numpy as np

from prolothar_common import validate
from prolothar_ca.ca.methods.countor.background_knowledge import BackgroundKnowledge, BackgroundKnowledgeNotApplicableError, NoBackgroundKnowledge, ObjectFeatureBackgroundKnowledge
from prolothar_ca.ca.methods.countor.order import ObjectOrder, OrderByFeature, OrderByObjectId
from prolothar_ca.ca.methods.countor.utils import get_variable_name_for_dimension

from prolothar_ca.ca.methods.method import CaMethod
from prolothar_ca.model.ca.constraints.boolean import RelationIsTrue
from prolothar_ca.model.ca.constraints.constraint import CaConstraint
from prolothar_ca.model.ca.constraints.numeric import Constant, CountConsecutive, GreaterOrEqual, LessOrEqual
from prolothar_ca.model.ca.constraints.quantifier import ForAll
from prolothar_ca.model.ca.constraints.query import AllOfType, AllOfTypeOrderBy, Filter, Product
from prolothar_ca.model.ca.example import CaExample
from prolothar_ca.model.ca.relation import CaRelationType
from prolothar_ca.model.ca.targets import CaTarget, RelationTarget

from prolothar_ca.model.ca import CaDataset
from prolothar_ca.model.ca.variable_type import CaBoolean, CaNumber

ConstraintSet = dict[tuple[str, str, str], ForAll]

class CountOr(CaMethod):
    """
    interface to CountOr from the paper
    "Automating Personnel Rostering by Learning Constraints Using Tensors"
    by Kumar et al. at ICTAI 2019
    """

    def acquire_constraints(self, dataset: CaDataset, target: CaTarget) -> list[CaConstraint]:
        validate.is_true(
            all(example.is_valid_solution for example in dataset),
            msg='countor requires positive examples only'
        )
        if not isinstance(target, RelationTarget):
            raise NotImplementedError()
        constraint_set_list = []
        for example in dataset:
            constraint_set_list.append(self.__constraint_list_to_set(
                self.__acquire_constraints_for_example(
                    example, target.relation_name, dataset
                )
            ))
        return list(reduce(self.__reduce_constraint_sets, constraint_set_list).values())

    def __constraint_list_to_set(
            self, constraint_list: list[ForAll]) -> ConstraintSet:
        """
        converts the given list of <= and >= constraints into a dictionary where
        the constraint without its value (e.g. "for all a in A: a.b <=")
        is used as key. this representation can then be used to efficiently merge
        the constraints (e.g. "x <= 42" and "x <= 47" are merged to "x <= 47").
        """
        return {
            (str(for_all.query), str(for_all.constraint.a), str(type(for_all.constraint))): for_all
            for for_all in constraint_list
        }

    def __reduce_constraint_sets(
            self, constraint_set_a: ConstraintSet,
            constraint_set_b: ConstraintSet) -> ConstraintSet:
        reduced_constraint_set = {}
        for constraint_key, constraint_a in constraint_set_a.items():
            try:
                constraint_b = constraint_set_b[constraint_key]
                if constraint_a.constraint.is_more_restrictive(constraint_b.constraint):
                    reduced_constraint_set[constraint_key] = constraint_b
                else:
                    reduced_constraint_set[constraint_key] = constraint_a
            except KeyError:
                reduced_constraint_set[constraint_key] = constraint_a
        for constraint_key, constraint_b in constraint_set_b.items():
            if constraint_key not in constraint_set_a:
                reduced_constraint_set[constraint_key] = constraint_b
        return reduced_constraint_set

    def __acquire_constraints_for_example(
            self, example: CaExample, relation_name: str, dataset: CaDataset):
        target_tensor = map_to_target_tensor(example, dataset.get_relation_type(relation_name))
        background_knowledge_list = self.__map_to_background_knowledge_list(
            example, relation_name, dataset)
        constraint_list = self.__find_bounding_constraints(target_tensor, relation_name, dataset)

        for background_knowledge in background_knowledge_list:
            try:
                constraint_list.extend(self.__find_bounding_constraints(
                    target_tensor, relation_name, dataset,
                    background_knowledge=background_knowledge))
            except BackgroundKnowledgeNotApplicableError:
                pass

        for order in self.__map_to_order_list(example, relation_name, dataset):
            ordered_target_tensor = map_to_target_tensor(
                example, dataset.get_relation_type(relation_name), order=order)
            constraint_list.extend(self.__find_consecutive_constraints(
                ordered_target_tensor, order, relation_name, dataset, example))
            for background_knowledge in background_knowledge_list:
                constraint_list.extend(self.__find_consecutive_constraints(
                    ordered_target_tensor, order, relation_name, dataset,
                    example, background_knowledge=background_knowledge))

        return constraint_list

    def __find_bounding_constraints(
            self, target_tensor: np.ndarray, relation_name: str,
            dataset: CaDataset,
            background_knowledge: BackgroundKnowledge = NoBackgroundKnowledge()) -> list[CaConstraint]:
        target_tensor = background_knowledge.filter_target_tensor(target_tensor)
        parameter_types = dataset.get_relation_type(relation_name).parameter_types
        parameter_names = tuple(get_variable_name_for_dimension(i) for i in range(len(parameter_types)))
        target_relation_filter = RelationIsTrue(
            dataset.get_relation_type(relation_name), parameter_names)
        constraints = []
        for m,s in self.__enumerate_splits(target_tensor):
            count_x_m_s =  np.sum(target_tensor, axis=tuple(s))
            trivial_upper_bound = np.max(target_tensor) * reduce(
                lambda a,b: a*b, (target_tensor.shape[s_i] for s_i in s))
            trivial_lower_bound = np.min(target_tensor)
            quantifier_query = self.__create_quantifier_query(parameter_types, parameter_names, m)

            if len(s) == 1:
                source_filter = Filter(
                    AllOfType(parameter_types[s[0]], parameter_names[s[0]]),
                    target_relation_filter
                )
            else:
                source_filter = Filter(
                    Product([
                        AllOfType(parameter_types[s_i], parameter_names[s_i])
                        for s_i in s
                    ]),
                    target_relation_filter
                )

            constraint_query = background_knowledge.create_constraint_query(source_filter)
            upper_bound = count_x_m_s.max()
            if upper_bound != trivial_upper_bound:
                constraints.append(ForAll(
                    quantifier_query,
                    LessOrEqual(
                        constraint_query,
                        Constant(upper_bound)
                    )
                ))
            lower_bound = count_x_m_s.min()
            if lower_bound != trivial_lower_bound:
                constraints.append(ForAll(
                    quantifier_query,
                    GreaterOrEqual(
                        constraint_query,
                        Constant(lower_bound)
                    )
                ))
        return constraints

    def __find_consecutive_constraints(
            self, target_tensor: np.ndarray, order: ObjectOrder, relation_name: str,
            dataset: CaDataset, example: CaExample,
            background_knowledge: BackgroundKnowledge = NoBackgroundKnowledge()) -> list[CaConstraint]:
        if not background_knowledge.is_boolean:
            return []
        target_tensor = background_knowledge.filter_target_tensor(target_tensor)
        parameter_types = dataset.get_relation_type(relation_name).parameter_types
        parameter_names = tuple(get_variable_name_for_dimension(i) for i in range(len(parameter_types)))

        constraints = []
        # for all x1 in employee: count_consecutive(x2 in shift | works_at_shift(x1,x2) order by x2.start_time, shifts_are_within_one_day(a,b)) >= 2
        for m,s in self.__enumerate_splits(target_tensor):
            quantifier_query = self.__create_quantifier_query(parameter_types, parameter_names, m)
            if len(s) == 1 and isinstance(order, OrderByFeature) and order.type_name == parameter_types[s[0]]:
                for relation_type in dataset.get_relation_types():
                    if isinstance(relation_type.value_type, CaBoolean) \
                    and relation_type.parameter_types == [order.type_name, order.type_name]:
                        trivial_upper_bound = target_tensor.shape[s[0]]
                        trivial_lower_bound = 1
                        query = CountConsecutive(
                            Filter(
                                AllOfTypeOrderBy(order.type_name, parameter_names[s[0]], order.feature_name),
                                background_knowledge.extend_filter(
                                    RelationIsTrue(dataset.get_relation_type(relation_name), parameter_names)
                                )
                            ),
                            'a', 'b', RelationIsTrue(relation_type, ('a', 'b'))
                        )
                        count_m_s = [
                            query.evaluate(example, quantified_variables)
                            for quantified_variables in quantifier_query.evaluate(example, {})
                        ]
                        upper_bound = max(max(row) for row in count_m_s)
                        if upper_bound != trivial_upper_bound:
                            constraints.append(ForAll(
                                quantifier_query,
                                LessOrEqual(
                                    query.maximum(),
                                    Constant(upper_bound)
                                )
                            ))
                        lower_bound = min(min(row) for row in count_m_s)
                        if lower_bound != trivial_lower_bound:
                            constraints.append(ForAll(
                                quantifier_query,
                                GreaterOrEqual(
                                    query.minimum(),
                                    Constant(lower_bound)
                                )
                            ))
        return constraints

    def __create_quantifier_query(self, parameter_types, parameter_names, m):
        if len(m) == 1:
            return AllOfType(parameter_types[m[0]], parameter_names[m[0]])
        else:
            return Product([
                AllOfType(parameter_types[m_i], parameter_names[m_i])
                for m_i in m
            ])

    def __enumerate_splits(self, target_tensor: np.ndarray) -> Generator[tuple[list[int], list[int]],None,None]:
        all_dimensions = set(range(len(target_tensor.shape)))
        for m in powerset(all_dimensions):
            s = all_dimensions.difference(m)
            if m and s:
                yield list(m), list(s)

    def __map_to_background_knowledge_list(
            self, example: CaExample, relation_name: str,
            dataset: CaDataset) -> list[BackgroundKnowledge]:
        dimension_parameters = dataset.get_relation_type(relation_name).parameter_types
        background_knowledge_list = []
        for object_type in dataset.get_object_types():
            all_objects_of_type = sorted(
                example.all_objects_per_type.get(object_type.name, set()),
                key=lambda o: o.object_id
            )
            for feature_name, feature_type in object_type.feature_definition.items():
                tensor = np.array([
                    [
                        float(an_object.features[feature_name])
                        if i == j else 0
                        for j in range(len(all_objects_of_type))
                    ]
                    for i, an_object in enumerate(all_objects_of_type)
                    if not isinstance(feature_type, CaBoolean) or an_object.features[feature_name]
                ])
                #filter out trivial filters that apply to no or all objects
                if len(tensor.shape) == 2 and tensor.shape[0] == tensor.shape[1] and not np.all(np.equal(tensor, np.identity(tensor.shape[0]))):
                    for dimension_index in [i for i,t in enumerate(dimension_parameters) if t == object_type.name]:
                        background_knowledge_list.append(ObjectFeatureBackgroundKnowledge(
                            tensor, dimension_index,
                            isinstance(object_type.feature_definition[feature_name], CaBoolean),
                            object_type.name, feature_name))
        return background_knowledge_list

    def __map_to_order_list(
            self, example: CaExample, relation_name_list: list[str],
            dataset: CaDataset) -> list[ObjectOrder]:
        order_list = []
        for object_type in dataset.get_object_types():
            all_objects_of_type = sorted(
                example.all_objects_per_type.get(object_type.name, set()),
                key=lambda o: o.object_id
            )
            for feature_name, feature_type in object_type.feature_definition.items():
                if isinstance(feature_type, CaNumber) \
                and len(set(o.features[feature_name] for o in all_objects_of_type)) > 1:
                    order_list.append(OrderByFeature(object_type.name, feature_name))
        return order_list

    def __repr__(self):
        return 'CountOr'

def map_to_target_tensor(
        example: CaExample,
        target_relation: CaRelationType,
        order: ObjectOrder = OrderByObjectId()):
    tensor = np.zeros(tuple(
        len(example.all_objects_per_type[t]) for t in target_relation.parameter_types))
    object_type_and_id_to_index = create_object_type_and_id_to_index(example, target_relation, order=order)
    for relation in example.relations[target_relation.name]:
        if relation.value:
            tensor_index = tuple([
                object_type_and_id_to_index[o.type_name][o.object_id]
                for o in relation.objects
            ])
            tensor[tensor_index] = 1
    return tensor

def create_object_type_and_id_to_index(
        example: CaExample, target_relation: CaRelationType,
        order: ObjectOrder = OrderByObjectId()) -> dict[str, dict[str, int]]:
    object_type_and_id_to_index = {}
    for object_type in target_relation.parameter_types:
        object_id_to_index = {}
        for an_object in order.sort_objects(example.all_objects_per_type[object_type]):
            object_id_to_index[an_object.object_id] = len(object_id_to_index)
        object_type_and_id_to_index[object_type] = object_id_to_index
    return object_type_and_id_to_index