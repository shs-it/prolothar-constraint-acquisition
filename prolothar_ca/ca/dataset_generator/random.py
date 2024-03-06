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

import datetime
import os
from itertools import product
from random import Random

import pandas as pd
from prolothar_common import validate
from prolothar_ca.ca.dataset_generator.dataset_generator import \
    CaDatasetGenerator
from prolothar_ca.model.ca.constraints.constraint import CaConstraint
from prolothar_ca.model.ca.dataset import CaDataset
from prolothar_ca.model.ca.example import CaExample
from prolothar_ca.model.ca.obj import CaObject, CaObjectType
from prolothar_ca.model.ca.relation import CaRelation, CaRelationType
from prolothar_ca.model.ca.targets import CaTarget, RelationTarget
from prolothar_ca.model.ca.variable_type import CaBoolean, CaNumber

TARGET_RELATION_NAME = 'z'

class RandomCaDatasetGenerator(CaDatasetGenerator):
    """
    a random dataset where there is no connection between features and
    target variable, i.e. the list of ground-truth constraints is empty
    """

    def __init__(
            self, dimensions: int = 2, nr_of_objects: int = 10,
            boolean_features: int = 2, numeric_features: int = 2, numeric_values: int = 5):
        self.__dimensions = dimensions
        self.__nr_of_objects = nr_of_objects
        self.__boolean_features = boolean_features
        self.__numeric_features = numeric_features
        self.__numeric_values = numeric_values
        self.__all_objects_per_type = None

    def _create_empty_dataset(self) -> CaDataset:
        return CaDataset(
            {
                f'O{i}': CaObjectType(
                    f'O{i}',
                    {
                        f'b{j}': CaBoolean()
                        for j in range(self.__boolean_features)
                    } | {
                        f'n{j}': CaNumber()
                        for j in range(self.__numeric_features)
                    }
                )
                for i in range(self.__dimensions)
            },
            {
                TARGET_RELATION_NAME: CaRelationType(
                    TARGET_RELATION_NAME,
                    tuple(f'O{i}' for i in range(self.__dimensions)),
                    CaBoolean()
                ),
            }
        )

    def _generate_positive_example(self, random_generator: Random) -> CaExample:
        if self.__all_objects_per_type is None:
            self.__all_objects_per_type = {
                f'O{i}': set(
                    self.__generate_object(f'O{i}.{j}', f'O{i}', random_generator)
                    for j in range(self.__nr_of_objects)
                )
                for i in range (self.__dimensions)
            }
        return CaExample(
            self.__all_objects_per_type,
            {
                TARGET_RELATION_NAME: {
                    CaRelation(TARGET_RELATION_NAME, objects, random_generator.choice((True, False)))
                    for objects in product(*[self.__all_objects_per_type[f'O{i}'] for i in range(self.__dimensions)])
                }
            },
            True
        )

    def __generate_object(self, object_id: str, type_name: str, random_generator: Random) -> CaObject:
        return CaObject(object_id, type_name, {
            f'b{i}': random_generator.choice((True, False))
            for i in range(self.__boolean_features)
        } | {
            f'n{i}': random_generator.randint(1, self.__numeric_values)
            for i in range(self.__numeric_features)
        })

    def _generate_negative_example(self, random_generator: Random) -> CaExample:
        raise NotImplementedError('only positive examples are supported')

    def get_ground_truth_constraints(self) -> list[CaConstraint]:
        return []

    def get_target(self) -> CaTarget:
        return RelationTarget(TARGET_RELATION_NAME)

