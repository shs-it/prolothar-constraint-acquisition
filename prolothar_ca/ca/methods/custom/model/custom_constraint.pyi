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

import abc
from typing import Union
from _typeshed import Incomplete
from abc import ABC, abstractmethod
import numpy as np
from prolothar_ca.model.ca.constraints.constraint import CaConstraint as CaConstraint
from prolothar_ca.model.ca.relation import CaRelationType as CaRelationType
from prolothar_ca.ca.methods.custom.model.cross_product_filter import CrossProductFilter as CrossProductFilter
from prolothar_ca.model.ca.dataset import CaDataset as CaDataset
from prolothar_ca.model.ca.example import CaExample as CaExample
from prolothar_ca.model.ca.obj import CaObject as CaObject, CaObjectType as CaObjectType
from prolothar_ca.model.ca.relation import CaRelation as CaRelation, CaRelationType as CaRelationType
from prolothar_ca.model.sat.cnf import CnfDisjunction as CnfDisjunction
from prolothar_ca.model.sat.variable import Variable
from typing import Optional

CONSTRAINT_TYPE_COST: float

class CustomConstraint(ABC, metaclass=abc.ABCMeta):
    encoded_model_length: Incomplete
    def __init__(self, encoded_model_length: float) -> None: ...
    @abstractmethod
    def compute_cnf_clauses(self, datagraph) -> set[CnfDisjunction]: ...
    @abstractmethod
    def merge(self, other: CustomConstraint) -> Optional['CustomConstraint']: ...
    @abstractmethod
    def to_ca_model(self, datagraph) -> CaConstraint: ...

class JoinTargetConstraint:
    encoded_model_length: Incomplete
    antecedent_terms: Incomplete
    consequent_term: Incomplete
    expected_value: Incomplete
    def __init__(self, antecedent_terms: list[tuple[int]], consequent_term: tuple[int], expected_value: bool, nr_of_target_relation_parameter_options: tuple[int]) -> None: ...
    def __eq__(self, other): ...
    def __hash__(self): ...
    def to_ca_model(self, target_relation_type: CaRelationType, variable_names: list[str]) -> CaConstraint: ...

class SingleTargetConstraint(CustomConstraint):
    antecedent_variables: Incomplete
    consequent_variable: Incomplete
    expected_value: Incomplete
    def __init__(self, antecedent_variables: list[int], consequent_variable: int, expected_value: bool, nr_of_variables: int) -> None: ...
    def compute_cnf_clauses(self, datagraph) -> set[CnfDisjunction]: ...
    def to_ca_model(self, datagraph) -> CaConstraint: ...
    def merge(self, other: CustomConstraint) -> Optional[CustomConstraint]: ...
    def count_true(self, dataset_np: np.ndarray) -> int: ...
    def count_true_by_consequent(self, dataset_np: np.ndarray) -> int: ...
    def __eq__(self, other): ...

class Partition:
    ...

class PartitionByTargetParameterFeaturesAreTrue(Partition):

    def __init__(
        self, parameter_index: int, target_relation_cardinality: int,
        feature_name_list: list[str], nr_of_boolean_features: int): ...

class PartitionByTargetParameterFeaturesAreFalse(Partition):

    def __init__(
        self, parameter_index: int, target_relation_cardinality: int,
        feature_name_list: list[str], nr_of_boolean_features: int): ...

class Count(CustomConstraint):
    is_trivial: bool

    def __init__(
        self, partition: Partition, lowerbound: int, upperbound: int, nr_of_target_variables: int,
        clause_cache: dict, is_trivial: bool = False): ...

    def get_nr_of_untrue_clauses_for_example(self, datagraph: DataGraph, example_id: int) -> int: ...

class DataGraph:
    def __init__(self, example: CaExample, dataset: CaDataset, target_relation: CaRelationType, max_nr_of_zeros: int = -1) -> None: ...
    def __del__(self) -> None: ...
    def add_object_type(self, object_type: CaObjectType): ...
    def add_object_node(self, an_object: CaObject, object_type: CaObjectType): ...
    def add_relation_node(self, relation: CaRelation): ...
    def add_target_relation_type(self, relation_type: CaRelationType): ...
    def add_target_relation_node(self, relation: CaRelation): ...
    def get_nr_of_target_variables(self) -> int: ...
    def get_target_variable(self, relation: CaRelation) -> Variable: ...
    def get_target_variable_by_number(self, variable_nr: int) -> Variable: ...
    def get_target_variables(self) -> dict[int, Variable]: ...
    def get_target_relation_type(self) -> CaRelationType: ...
    def get_target_relation(self, variable_nr: int) -> CaRelation: ...
    def compute_cnf_clauses(self, target_constraint: JoinTargetConstraint, additional_joins: tuple[int], cross_product_filter: CrossProductFilter) -> set[CnfDisjunction]: ...
    def query_variables(self, target_constraint: JoinTargetConstraint, additional_joins: tuple[int], cross_product_filter: CrossProductFilter) -> list[tuple[Variable]]: ...
    def get_feature_value_bounds(self, object_type: str, feature_name: str) -> tuple[Union[int, float], Union[int, float]]: ...
    def get_target_variables_grouped_by_parameter_with_true_features(self, parameter_index: int, feature_name_list: list[str]) -> tuple[tuple[Variable]]: ...
    def clear_caches(self): ...