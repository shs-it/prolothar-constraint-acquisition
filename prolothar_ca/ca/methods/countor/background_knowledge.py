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

from abc import ABC
from dataclasses import dataclass
import numpy as np
from prolothar_ca.ca.methods.countor.utils import get_variable_name_for_dimension

from prolothar_ca.model.ca.constraints.numeric import AggregateSum, Count, NumericExpression, NumericFeature
from prolothar_ca.model.ca.constraints.query import Filter, Query

class BackgroundKnowledgeNotApplicableError(Exception):
    pass

@dataclass
class BackgroundKnowledge(ABC):
    filter_tensor: np.ndarray
    dimension_index: int
    is_boolean: bool

    def filter_target_tensor(self, target_tensor: np.ndarray) -> np.ndarray:
        if self.dimension_index == 0:
            filtered_target_tensor = target_tensor
        else:
            permutation = (self.dimension_index,) + tuple(
                d for d in range(len(target_tensor.shape))
                if d != self.dimension_index
            )
            filtered_target_tensor = target_tensor.transpose(permutation)

        try:
            filtered_target_tensor = np.matmul(self.filter_tensor, filtered_target_tensor)
        except ValueError:
            raise BackgroundKnowledgeNotApplicableError()

        if self.dimension_index > 0:
            inverse_permutation = tuple(i for i,_ in sorted(enumerate(permutation), key=lambda x: x[1]))
            filtered_target_tensor = filtered_target_tensor.transpose(inverse_permutation)

        return filtered_target_tensor

    def create_constraint_query(self, source_filter: Filter) -> Query:
        if self.is_boolean:
            return Count(self.extend_filter(source_filter))
        else:
            return AggregateSum(
                self._get_numeric_expression(),
                source_filter
            )

class NoBackgroundKnowledge(BackgroundKnowledge):
    def __init__(self):
        super().__init__(None, None, True)
    def filter_target_tensor(self, target_tensor: np.ndarray) -> np.ndarray:
        return target_tensor
    def extend_filter(self, filter: Filter):
        return filter

@dataclass
class ObjectFeatureBackgroundKnowledge(BackgroundKnowledge):
    object_type: str
    feature: str

    def _get_numeric_expression(self) -> NumericExpression:
        return NumericFeature(
            self.object_type,
            get_variable_name_for_dimension(self.dimension_index),
            self.feature
        )

@dataclass
class RelationBackgroundKnowledge(BackgroundKnowledge):
    relation_type: str