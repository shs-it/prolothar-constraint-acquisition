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
from sortedcontainers import SortedSet

from prolothar_common.experiments.statistics import Statistics

from prolothar_ca.model.ca.dataset import CaDataset
from prolothar_ca.model.ca.relation import CaRelationType
from prolothar_ca.model.ca.variable_type import CaBoolean
from prolothar_ca.model.sat.variable import Value

from prolothar_ca.ca.methods.custom.model.custom_constraint import Count
from prolothar_ca.ca.methods.custom.model.custom_constraint import Partition
from prolothar_ca.ca.methods.custom.model.custom_constraint import PartitionByTargetParameterFeaturesAreTrue
from prolothar_ca.ca.methods.custom.model.custom_constraint import PartitionByTargetParameterFeaturesAreFalse
from prolothar_ca.ca.methods.custom.model.custom_constraint import DataGraph
from prolothar_ca.ca.methods.custom.sat_encoding import SatEncodedExample

def generate_count_candidates(
        dataset: CaDataset,
        sat_encoded_dataset: list[SatEncodedExample],
        datagraph: DataGraph,
        target_relation: CaRelationType) -> Generator[Count, None, None]:
    target_relation_cardinality = len(target_relation.parameter_types)
    clause_cache = {}
    nr_of_target_variables = datagraph.get_nr_of_target_variables()
    for i, parameter_type in enumerate(target_relation.parameter_types):
        nr_of_boolean_features = dataset.get_nr_of_boolean_features(parameter_type)
        yield from _generate_count_candidates_from_partition(
            PartitionByTargetParameterFeaturesAreTrue(i, target_relation_cardinality, [], nr_of_boolean_features),
            datagraph, sat_encoded_dataset, clause_cache, nr_of_target_variables)
        for feature_name, feature_type in dataset.get_object_type(parameter_type).feature_definition.items():
            if isinstance(feature_type, CaBoolean):
                yield from _generate_count_candidates_from_partition(
                    PartitionByTargetParameterFeaturesAreTrue(
                        i, target_relation_cardinality, [feature_name], nr_of_boolean_features
                    ),
                    datagraph, sat_encoded_dataset, clause_cache, nr_of_target_variables
                )
                yield from _generate_count_candidates_from_partition(
                    PartitionByTargetParameterFeaturesAreFalse(
                        i, target_relation_cardinality, [feature_name], nr_of_boolean_features
                    ),
                    datagraph, sat_encoded_dataset, clause_cache, nr_of_target_variables
                )
                for second_feature_name, second_feature_type in dataset.get_object_type(parameter_type).feature_definition.items():
                    if isinstance(second_feature_type, CaBoolean) and feature_name < second_feature_name:
                        yield from _generate_count_candidates_from_partition(
                            PartitionByTargetParameterFeaturesAreTrue(
                                i, target_relation_cardinality,
                                [feature_name, second_feature_name],
                                nr_of_boolean_features
                            ),
                            datagraph, sat_encoded_dataset, clause_cache, nr_of_target_variables
                        )

def _generate_count_candidates_from_partition(
        partition: Partition,
        datagraph: DataGraph,
        sat_encoded_dataset: list[SatEncodedExample],
        clause_cache: dict, nr_of_target_variables: int):
    variable_group_tuples = partition.compute_variable_groups(datagraph)
    if variable_group_tuples:
        statistics_of_counts = Statistics()
        sorted_set_of_counts = SortedSet()
        for example in sat_encoded_dataset:
            for variable_group in variable_group_tuples:
                count = _count_true_variables_in_group(variable_group, example)
                sorted_set_of_counts.add(count)
                statistics_of_counts.push(count)
        maximum_possible_upperbound = len(variable_group_tuples[0])
        for lowerbound in sorted_set_of_counts.irange(statistics_of_counts.minimum(), int(statistics_of_counts.mean())):
            for upperbound in sorted_set_of_counts.irange(max(lowerbound, int(statistics_of_counts.mean())), statistics_of_counts.maximum()):
                yield Count(
                    partition, lowerbound, upperbound, nr_of_target_variables, clause_cache,
                    is_trivial = (
                        lowerbound == 0 and
                        upperbound == maximum_possible_upperbound
                    )
                )

def _count_true_variables_in_group(variable_group: tuple, example: SatEncodedExample):
    count = 0
    for variable in variable_group:
        if example[variable].value == Value.TRUE:
            count += 1
    return count