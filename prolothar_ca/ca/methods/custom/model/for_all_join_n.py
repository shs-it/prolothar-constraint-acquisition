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

from collections import defaultdict
from itertools import chain, repeat
from math import log2
from prolothar_common.mdl_utils import L_N
from prolothar_ca.ca.methods.custom.model.custom_constraint import DataGraph

from prolothar_ca.ca.methods.custom.model.cross_product_filter import CrossProductFilter
from prolothar_ca.ca.methods.custom.model.custom_constraint import CustomConstraint
from prolothar_ca.ca.methods.custom.model.custom_constraint import JoinTargetConstraint
from prolothar_ca.model.ca.constraints.constraint import CaConstraint
from prolothar_ca.model.ca.constraints.quantifier import ForAll
from prolothar_ca.model.ca.constraints.query import Filter, Product, AllOfType
from prolothar_ca.model.sat.cnf import CnfDisjunction

class ForAllJoinN(CustomConstraint):

    def __init__(self, join_index: int, nr_of_joins: int, cross_product_filter: CrossProductFilter, target_constraint: JoinTargetConstraint, target_relation_cardinality: int):
        super().__init__(
            log2(target_relation_cardinality) + L_N(nr_of_joins) +
            cross_product_filter.encoded_model_length +
            target_constraint.encoded_model_length
        )
        self.join_index = join_index
        self.nr_of_joins = nr_of_joins
        self.cross_product_filter = cross_product_filter
        self.target_constraint = target_constraint
        self.target_relation_cardinality = target_relation_cardinality

    def compute_cnf_clauses(self, datagraph: DataGraph, term_factory) -> set[CnfDisjunction]:
        return datagraph.compute_cnf_clauses(
            self.target_constraint,
            tuple(self.join_index for _ in range(self.nr_of_joins)),
            self.cross_product_filter)

    def merge(self, other: CustomConstraint) -> None|CustomConstraint:
        if isinstance(other, ForAllJoinN) \
        and self.join_index == other.join_index \
        and self.nr_of_joins == other.nr_of_joins \
        and self.target_constraint == other.target_constraint:
            return ForAllJoinN(
                self.join_index, self.nr_of_joins,
                self.cross_product_filter | other.cross_product_filter, self.target_constraint,
                self.target_relation_cardinality)
        else:
            return None

    def to_ca_model(self, datagraph) -> CaConstraint:
        target_relation = datagraph.get_target_relation_type()
        object_type_count = defaultdict(int)
        parameter_type_list = list(chain(
            target_relation.parameter_types,
            (target_relation.parameter_types[self.join_index] for _ in range(self.nr_of_joins))))
        variable_names = []
        for parameter_type in parameter_type_list:
            parameter_type_count = object_type_count[parameter_type]
            if parameter_type_count == 0:
                variable_suffix = ''
            else:
                variable_suffix = str(parameter_type_count + 1)
            variable_names.append(f'{parameter_type}{variable_suffix}')
            object_type_count[parameter_type] += 1
        return ForAll(
            Filter(
                Product([
                    AllOfType(parameter_type, variable)
                    for parameter_type, variable in zip(
                        parameter_type_list,
                        variable_names
                    )
                ]),
                self.cross_product_filter.to_ca_model(
                    target_relation,
                    tuple(self.join_index for _ in range(self.nr_of_joins)),
                    variable_names
                )
            ),
            self.target_constraint.to_ca_model(target_relation, variable_names)
        )

    def __repr__(self):
        return f'ForAllJoinN({self.nr_of_joins}x{self.join_index}, {self.cross_product_filter}, {self.target_constraint})'
