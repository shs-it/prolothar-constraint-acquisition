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

from typing import Generator
from math import ceil
from itertools import combinations, chain
from more_itertools import ilen
from prolothar_ca.ca.methods.custom.model.cross_product_filter import BooleanRelation
from prolothar_ca.ca.methods.custom.model.cross_product_filter import NumericFilter
from prolothar_ca.ca.methods.custom.model.cross_product_filter import NotCrossProductFilter
from prolothar_ca.ca.methods.custom.model.cross_product_filter import BooleanFeature
from prolothar_ca.ca.methods.custom.model.cross_product_filter import BooleanFeaturesNotEqual
from prolothar_ca.ca.methods.custom.model.cross_product_filter import NumericFeature
from prolothar_ca.ca.methods.custom.model.cross_product_filter import AndCrossProductFilter
from prolothar_ca.ca.methods.custom.model.cross_product_filter import Absolute
from prolothar_ca.ca.methods.custom.model.cross_product_filter import Difference
from prolothar_ca.ca.methods.custom.model.cross_product_filter import IntegerConstant
from prolothar_ca.ca.methods.custom.model.for_all_no_join import ForAll
from prolothar_ca.ca.methods.custom.model.custom_constraint import JoinTargetConstraint
from prolothar_ca.model.ca.dataset import CaDataset
from prolothar_ca.model.ca.relation import CaRelationType
from prolothar_ca.model.ca.variable_type import CaBoolean, CaNumber

def generate_for_all_cross_product_candidates(
        dataset: CaDataset,
        target_relation: CaRelationType,
        nr_of_target_relation_parameter_options: tuple[int],
        create_feature_distance_candidates: bool = False,
        is_for_planning_dataset: bool = False) -> Generator[ForAll, None, None]:
    crossproduct_cardinality = len(nr_of_target_relation_parameter_options)
    target_constraint_true = JoinTargetConstraint(
        [], tuple(range(crossproduct_cardinality)), True,
        nr_of_target_relation_parameter_options)
    target_constraint_false = JoinTargetConstraint(
        [], tuple(range(crossproduct_cardinality)), False,
        nr_of_target_relation_parameter_options)
    non_target_relations = [r for r in dataset.get_relation_types() if r != target_relation]
    nr_of_boolean_relations = ilen(r for r in non_target_relations if isinstance(r.value_type, CaBoolean))
    for i in range(len(nr_of_target_relation_parameter_options)):
        object_type_i = dataset.get_object_type(target_relation.parameter_types[i])
        for cross_product_filter in _generate_cross_product_filter_from_features(
                i, object_type_i, crossproduct_cardinality):
            if not is_for_planning_dataset:
                yield ForAll(cross_product_filter, target_constraint_true)
            yield ForAll(cross_product_filter, target_constraint_false)
        for j in range(i+1, crossproduct_cardinality):
            object_type_j = dataset.get_object_type(target_relation.parameter_types[j])
            if object_type_i == object_type_j:
                for cross_product_filter in _generate_cross_product_filter_from_feature_pairs(
                        i, j, object_type_i, crossproduct_cardinality,
                        dataset, target_relation, create_feature_distance_candidates):
                    if not is_for_planning_dataset:
                        yield ForAll(cross_product_filter, target_constraint_true)
                    yield ForAll(cross_product_filter, target_constraint_false)
            for cross_product_filter in _generate_cross_product_filter_queries_from_relations(
                    i, j, object_type_i, object_type_j, non_target_relations,
                    crossproduct_cardinality, nr_of_boolean_relations):
                if not is_for_planning_dataset:
                    yield ForAll(cross_product_filter, target_constraint_true)
                yield ForAll(cross_product_filter, target_constraint_false)
    _check_there_are_no_relations_without_parameters(dataset)

def _generate_cross_product_filter_queries_from_relations(
        i, j, object_type_i, object_type_j, non_target_relations: list[CaRelationType],
        crossproduct_cardinality: int, nr_of_boolean_relations):
    for relation in non_target_relations:
        if len(relation.parameter_types) == 2:
            if relation.parameter_types[0] == object_type_i.name \
            and relation.parameter_types[1] == object_type_j.name:
                relation_filter = BooleanRelation(relation, (i,j), crossproduct_cardinality, nr_of_boolean_relations)
                yield relation_filter
                yield NotCrossProductFilter(relation_filter)
            if relation.parameter_types[1] == object_type_i.name \
            and relation.parameter_types[0] == object_type_j.name:
                relation_filter = BooleanRelation(relation, (j,i), crossproduct_cardinality, nr_of_boolean_relations)
                yield relation_filter
                yield NotCrossProductFilter(relation_filter)

def _generate_cross_product_filter_from_features(
        i: int, object_type, crossproduct_cardinality: int):
    boolean_features = [
        feature_name for feature_name, feature_type in object_type.feature_definition.items()
        if isinstance(feature_type, CaBoolean)
    ]
    nr_of_boolean_features = len(boolean_features)
    for feature_name, feature_type in object_type.feature_definition.items():
        if isinstance(feature_type, CaBoolean):
            boolean_filter = BooleanFeature(feature_name, i, crossproduct_cardinality, nr_of_boolean_features)
            yield boolean_filter
            yield NotCrossProductFilter(boolean_filter)

def _generate_cross_product_filter_from_feature_pairs(
        i: int, j: int, object_type, crossproduct_cardinality: int,
        dataset: CaDataset, target_relation: CaRelationType, create_feature_distance_candidates: bool):
    boolean_features = [
        feature_name for feature_name, feature_type in object_type.feature_definition.items()
        if isinstance(feature_type, CaBoolean)
    ]
    nr_of_boolean_features = len(boolean_features)
    for feature_a, feature_b in chain(combinations(boolean_features, 2), zip(boolean_features,boolean_features)):
        yield AndCrossProductFilter([
            BooleanFeature(feature_a, i, crossproduct_cardinality, nr_of_boolean_features),
            BooleanFeature(feature_b, j, crossproduct_cardinality, nr_of_boolean_features)
        ])
        yield BooleanFeaturesNotEqual(
            feature_a, i, feature_b, j,
            crossproduct_cardinality, nr_of_boolean_features
        )
    numeric_features = [
        feature_name for feature_name, feature_type in object_type.feature_definition.items()
        if isinstance(feature_type, CaNumber)
    ]
    for feature_a, feature_b in chain(combinations(numeric_features, 2), zip(numeric_features,numeric_features)):
            left_feature = NumericFeature(
                feature_a, i, crossproduct_cardinality, len(numeric_features))
            right_feature = NumericFeature(
                feature_b, j, crossproduct_cardinality, len(numeric_features))
            yield NumericFilter(left_feature, NumericFilter.EQ, right_feature)
            yield NumericFilter(left_feature, NumericFilter.LE, right_feature)
            yield NumericFilter(left_feature, NumericFilter.GT, right_feature)
            yield NumericFilter(right_feature, NumericFilter.LE, left_feature)
            yield NumericFilter(right_feature, NumericFilter.GT, left_feature)
            if create_feature_distance_candidates and feature_a != feature_b:
                absolute_difference_filter_left = Absolute(Difference(
                    left_feature, left_feature
                ))
                absolute_difference_filter_right = Absolute(Difference(
                    right_feature, right_feature
                ))
                yield NumericFilter(absolute_difference_filter_left, NumericFilter.LE, right_feature)
                yield NumericFilter(absolute_difference_filter_left, NumericFilter.GT, right_feature)
                yield NumericFilter(absolute_difference_filter_right, NumericFilter.LE, left_feature)
                yield NumericFilter(absolute_difference_filter_right, NumericFilter.GT, left_feature)
    if create_feature_distance_candidates:
        for feature_name in numeric_features:
            max_absolute_difference = IntegerConstant(_compute_max_absolute_difference(
                dataset, target_relation, feature_name, i, j))
            absolute_difference_filter = Absolute(Difference(
                NumericFeature(feature_name, i, crossproduct_cardinality, len(numeric_features)),
                NumericFeature(feature_name, j, crossproduct_cardinality, len(numeric_features)),
            ))
            yield NumericFilter(absolute_difference_filter, NumericFilter.LE, max_absolute_difference)
            yield NumericFilter(absolute_difference_filter, NumericFilter.GT, max_absolute_difference)

def _compute_max_absolute_difference(
        dataset: CaDataset, target_relation: CaRelationType,
        feature_name: str, i: int, j: int) -> int:
    max_difference = 0
    for example in dataset:
        for relation in example.relations[target_relation.name]:
            if relation.value:
                try:
                    difference = abs(
                        relation.objects[i].features[feature_name] -
                        relation.objects[j].features[feature_name]
                    )
                except KeyError:
                    raise NotImplementedError((
                        target_relation, i, j, feature_name,
                        target_relation.parameter_types[i],
                        target_relation.parameter_types[j],
                        relation.objects[i].features.keys(),
                        relation.objects[j].features.keys())
                    )
                if difference > max_difference:
                    max_difference = difference
    return int(ceil(max_difference))

def _check_there_are_no_relations_without_parameters(dataset):
    for relation_type in dataset.get_relation_types():
        if not relation_type.parameter_types:
            raise NotImplementedError((
                'empty relations/predicates are not supported.\n'
                f'e.g. replace the empty predicate {relation_type.name} with two objects with a boolean feature,\n'
                'where one object represents True and the other object represents False and\n'
                'set their boolean feature accordingly. alternatively, remove it.'
            ))