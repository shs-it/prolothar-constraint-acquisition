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

import os
from random import Random
import pickle

from prolothar_common import validate
from prolothar_ca.ca.dataset_generator.dataset_generator import \
    CaDatasetGenerator
from prolothar_ca.model.ca.constraints.constraint import CaConstraint
from prolothar_ca.model.ca.dataset import CaDataset
from prolothar_ca.model.ca.example import CaExample
from prolothar_ca.model.ca.obj import CaObject, CaObjectType
from prolothar_ca.model.ca.relation import CaRelation, CaRelationType
from prolothar_ca.model.ca.targets import CaTarget, RelationTarget
from prolothar_ca.model.ca.variable_type import CaBoolean
from prolothar_ca.model.ca.constraints.quantifier import ForAll
from prolothar_ca.model.ca.constraints.query import Product, AllOfType, Filter
from prolothar_ca.model.ca.constraints.numeric import Count, Equal, Constant
from prolothar_ca.model.ca.constraints.boolean import RelationIsTrue, RelationIsFalse
from prolothar_ca.model.ca.constraints.conjunction import Implies

NODE_TYPE = 'Node'
COLOR_TYPE = 'Color'
HAS_EDGE_RELATION = 'has_edge'
HAS_COLOR_RELATION = 'has_color'

class PickleCaDatasetGenerator(CaDatasetGenerator):
    """
    loads a CaDataset from a pickle file
    """

    def __init__(self, pickle_file: str, target_relation: str):
        validate.is_true(os.path.exists(pickle_file))
        with open(pickle_file, 'rb') as f:
            self.__ca_dataset: CaDataset = pickle.load(f)
        self.__target_relation = target_relation
        self.__positive_examples = [
            example for example in self.__ca_dataset
            if example.is_valid_solution
        ]
        self.__negative_examples = [
            example for example in self.__ca_dataset
            if not example.is_valid_solution
        ]
        self.__positive_index = 0
        self.__negative_index = 0

    def _create_empty_dataset(self) -> CaDataset:
        return self.__ca_dataset.empty_copy()

    def generate(self, nr_of_positive_examples: int, nr_of_negative_examples: int, random_seed: int | None = None) -> CaDataset:
        validate.less_or_equal(nr_of_positive_examples, len(self.__positive_examples))
        validate.less_or_equal(nr_of_negative_examples, len(self.__negative_examples))
        random_generator = Random(random_seed)
        random_generator.shuffle(self.__positive_examples)
        random_generator.shuffle(self.__negative_examples)
        self.__positive_index = 0
        self.__negative_index = 0
        return super().generate(nr_of_positive_examples, nr_of_negative_examples, random_seed)

    def _generate_positive_example(self, random_generator: Random) -> CaExample:
        example = self.__positive_examples[self.__positive_index]
        self.__positive_index += 1
        return example

    def _generate_negative_example(self, random_generator: Random) -> CaExample:
        example = self.__negative_examples[self.__negative_index]
        self.__negative_index += 1
        return example

    def get_ground_truth_constraints(self) -> list[CaConstraint]:
        return []

    def get_target(self) -> CaTarget:
        return RelationTarget(self.__target_relation)
