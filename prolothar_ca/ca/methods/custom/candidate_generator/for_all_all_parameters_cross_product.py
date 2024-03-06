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

from itertools import product
from typing import Generator
from prolothar_ca.ca.methods.custom.model.cross_product_filter import CrossProductFilter, NullCrossProductFilter, NumericFeature, NumericFilter, AndCrossProductFilter
from prolothar_ca.ca.methods.custom.model.cross_product_filter import BooleanFeature
from prolothar_ca.ca.methods.custom.model.for_all_join_all import ForAllJoinAll
from prolothar_ca.ca.methods.custom.model.custom_constraint import JoinTargetConstraint
from prolothar_ca.model.ca.dataset import CaDataset
from prolothar_ca.model.ca.relation import CaRelationType
from prolothar_ca.model.ca.variable_type import CaBoolean, CaNumber

def generate_for_all_all_parameters_cross_product_candidates(
        dataset: CaDataset,
        target_relation: CaRelationType,
        nr_of_target_relation_parameter_options: tuple[int]):
    target_relation_cardinality = len(target_relation.parameter_types)
    left_join_indices = tuple(range(len(target_relation.parameter_types)))
    right_join_indices = tuple(i + target_relation_cardinality for i in left_join_indices)
    target_constraint_true = JoinTargetConstraint(
        [left_join_indices], right_join_indices, True,
        nr_of_target_relation_parameter_options)
    target_constraint_false = JoinTargetConstraint(
        [left_join_indices], right_join_indices, False,
        nr_of_target_relation_parameter_options)
    nr_of_numeric_features = tuple(
        dataset.get_nr_of_numeric_features(parameter_type)
        for parameter_type in target_relation.parameter_types
    )
    nr_of_boolean_features = tuple(
        dataset.get_nr_of_boolean_features(parameter_type)
        for parameter_type in target_relation.parameter_types
    )
    for cross_product_filter in _generate_filter_queries(
            dataset, target_relation, target_relation_cardinality,
            nr_of_numeric_features, nr_of_boolean_features):
        yield ForAllJoinAll(cross_product_filter, target_constraint_true, target_relation_cardinality)
        yield ForAllJoinAll(cross_product_filter, target_constraint_false, target_relation_cardinality)

def _generate_filter_queries(
        dataset: CaDataset,
        target_relation: CaRelationType,
        target_relation_cardinality: int,
        nr_of_numeric_features: tuple[int],
        nr_of_boolean_features: tuple[int]) -> Generator[CrossProductFilter, None, None]:
    for feature_filter_combination in product(*(
            _generate_feature_filters(
                object_type_name, i, dataset, target_relation_cardinality,
                nr_of_numeric_features[i], nr_of_boolean_features[i])
            for i,object_type_name in enumerate(target_relation.parameter_types))):
        filter_list = [f for f in feature_filter_combination if f is not None]
        if not filter_list:
            yield NullCrossProductFilter()
        elif len(filter_list) == 1:
            yield filter_list[0]
        else:
            yield AndCrossProductFilter(filter_list)

def _generate_feature_filters(
        object_type_name: str, left_index: int, dataset: CaDataset,
        target_relation_cardinality: int,
        nr_of_numeric_features_of_join_object: int,
        nr_of_boolean_features_of_join_object: int) -> Generator[CrossProductFilter, None, None]:
    object_type = dataset.get_object_type(object_type_name)
    for feature_name, feature_type in object_type.feature_definition.items():
        if isinstance(feature_type, CaNumber):
            left_feature = NumericFeature(
                feature_name, left_index,
                target_relation_cardinality,
                nr_of_numeric_features_of_join_object)
            right_feature = NumericFeature(
                feature_name, left_index + target_relation_cardinality,
                target_relation_cardinality,
                nr_of_numeric_features_of_join_object)
            yield NumericFilter(left_feature, NumericFilter.EQ, right_feature)
            yield NumericFilter(left_feature, NumericFilter.LE, right_feature)
            yield NumericFilter(left_feature, NumericFilter.GT, right_feature)
            yield NumericFilter(right_feature, NumericFilter.LE, left_feature)
            yield NumericFilter(right_feature, NumericFilter.GT, left_feature)
        elif isinstance(feature_type, CaBoolean):
            left_feature = BooleanFeature(
                feature_name, left_index,
                target_relation_cardinality,
                nr_of_boolean_features_of_join_object)
            right_feature = BooleanFeature(
                feature_name, left_index + target_relation_cardinality,
                target_relation_cardinality,
                nr_of_boolean_features_of_join_object)
            yield AndCrossProductFilter([left_feature, right_feature])
    yield None