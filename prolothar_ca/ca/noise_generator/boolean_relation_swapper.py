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

from random import Random
from math import ceil
from prolothar_common import validate

from prolothar_ca.model.ca.dataset import CaDataset
from prolothar_ca.model.ca.example import CaExample
from prolothar_ca.model.ca.variable_type import CaBoolean
from prolothar_ca.ca.noise_generator.single_example_noise_generator import SingleExampleNoiseGenerator
from prolothar_ca.ca.noise_generator.single_example_noise_generator import SingleExampleNoiseGenerator

class BooleanRelationSwapper(SingleExampleNoiseGenerator):
    """
    noise model that swaps a given proportion of boolean relation values.
    the noise-level refers to the minority value
    """

    def __init__(self, noise_proportion: float, relation_name: str, random_seed: int|None = None) -> None:
        validate.in_closed_interval(noise_proportion, 0, 1)
        self.__noise_proportion = noise_proportion
        self.__relation_name = relation_name
        self.__random = Random(random_seed)
        self.__random_seed = random_seed

    def validate_usage_on_dataset(self, dataset: CaDataset):
        validate.is_instance(dataset.get_relation_type(self.__relation_name).value_type, CaBoolean)

    def apply_on_example(self, example: CaExample):
        true_relations = [r for r in example.relations[self.__relation_name] if r.value]
        false_relations = [r for r in example.relations[self.__relation_name] if not r.value]
        if len(true_relations) > len(false_relations):
            majority_list = true_relations
            minority_list = false_relations
        else:
            majority_list = false_relations
            minority_list = true_relations
        self.__random.shuffle(majority_list)
        self.__random.shuffle(minority_list)
        round_function = int if self.__random.random() < 0.5 else ceil
        for i,relation in enumerate(minority_list[:round_function(self.__noise_proportion * len(minority_list))]):
            example.set_relation_value(relation, not relation.value)
            example.set_relation_value(majority_list[i], not majority_list[i].value)

    def __repr__(self):
        return f'BooleanRelationSwapper({self.__noise_proportion}, {self.__relation_name}, {self.__random_seed})'