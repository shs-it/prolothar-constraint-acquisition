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
from prolothar_ca.ca.methods.custom.model.cross_product_filter import CrossProductFilter, NullCrossProductFilter
from prolothar_ca.ca.methods.custom.model.cross_product_filter import NumericFilter
from prolothar_ca.ca.methods.custom.model.cross_product_filter import BooleanFeature
from prolothar_ca.ca.methods.custom.model.cross_product_filter import NumericFeature
from prolothar_ca.ca.methods.custom.model.cross_product_filter import BooleanRelation
from prolothar_ca.ca.methods.custom.model.cross_product_filter import AndCrossProductFilter
from prolothar_ca.ca.methods.custom.model.for_all_join_n import ForAllJoinN
from prolothar_ca.ca.methods.custom.model.custom_constraint import JoinTargetConstraint
from prolothar_ca.model.ca.dataset import CaDataset
from prolothar_ca.model.ca.obj import CaObjectType
from prolothar_ca.model.ca.relation import CaRelationType
from prolothar_ca.model.ca.variable_type import CaBoolean, CaNumber

def generate_for_all_one_parameter_cross_product_candidates(
        dataset: CaDataset,
        target_relation: CaRelationType,
        nr_of_target_relation_parameter_options: tuple[int]) -> Generator[ForAllJoinN, None, None]:
    left_join_indices = tuple(range(len(target_relation.parameter_types)))
    right_index = len(target_relation.parameter_types)
    nr_of_numeric_features = tuple(
        dataset.get_nr_of_numeric_features(parameter_type)
        for parameter_type in target_relation.parameter_types
    )
    nr_of_boolean_features = tuple(
        dataset.get_nr_of_boolean_features(parameter_type)
        for parameter_type in target_relation.parameter_types
    )
    nr_of_boolean_relations = dataset.get_total_nr_of_boolean_functions() - sum(nr_of_boolean_features)
    for join_index, join_type_name in enumerate(target_relation.parameter_types):
        right_join_indices = tuple(i if i != join_index else right_index for i in left_join_indices)
        nr_of_numeric_features_of_join_object = nr_of_numeric_features[join_index]
        nr_of_boolean_features_of_join_object = nr_of_boolean_features[join_index]
        target_constraint_true = JoinTargetConstraint(
            [left_join_indices], right_join_indices, True,
            nr_of_target_relation_parameter_options)
        target_constraint_false = JoinTargetConstraint(
            [left_join_indices], right_join_indices, False,
            nr_of_target_relation_parameter_options)
        for cross_product_filter in _generate_for_all_cross_product_filter_queries(
                dataset.get_object_type(join_type_name),
                join_index, right_index, nr_of_numeric_features_of_join_object,
                nr_of_boolean_features_of_join_object, nr_of_boolean_relations,
                [rt for rt in dataset.get_relation_types() if rt != target_relation]):
            yield ForAllJoinN(
                join_index, 1, cross_product_filter,
                target_constraint_true, right_index
            )
            yield ForAllJoinN(
                join_index, 1, cross_product_filter,
                target_constraint_false, right_index
            )

def _generate_for_all_cross_product_filter_queries(
        joined_object_type: CaObjectType, left_index: int, right_index: int,
        nr_of_numeric_features_of_join_object: int,
        nr_of_boolean_features_of_join_object: int,
        nr_of_boolean_relations: int,
        relation_types: list[CaRelationType]) -> Generator[CrossProductFilter|None, None, None]:
    yield NullCrossProductFilter()
    cross_product_cardinality = right_index + 1
    for feature_name, feature_type in joined_object_type.feature_definition.items():
        if isinstance(feature_type, CaNumber):
            left_feature = NumericFeature(
                feature_name, left_index,
                cross_product_cardinality,
                nr_of_numeric_features_of_join_object)
            right_feature = NumericFeature(
                feature_name, right_index,
                cross_product_cardinality,
                nr_of_numeric_features_of_join_object)
            yield NumericFilter(left_feature, NumericFilter.EQ, right_feature)
            yield NumericFilter(left_feature, NumericFilter.LE, right_feature)
            yield NumericFilter(left_feature, NumericFilter.GT, right_feature)
            yield NumericFilter(right_feature, NumericFilter.LE, left_feature)
            yield NumericFilter(right_feature, NumericFilter.GT, left_feature)
        elif isinstance(feature_type, CaBoolean):
            left_feature = BooleanFeature(
                feature_name, left_index,
                cross_product_cardinality,
                nr_of_boolean_features_of_join_object)
            right_feature = BooleanFeature(
                feature_name, right_index,
                cross_product_cardinality,
                nr_of_boolean_features_of_join_object)
            yield AndCrossProductFilter([left_feature, right_feature])
    for relation_type in relation_types:
        if isinstance(relation_type.value_type, CaBoolean) \
        and len(relation_type.parameter_types) == 2 \
        and relation_type.parameter_types[0] == joined_object_type.name \
        and relation_type.parameter_types[1] == joined_object_type.name:
            yield BooleanRelation(
                relation_type,
                (left_index, right_index),
                cross_product_cardinality,
                nr_of_boolean_relations
            )