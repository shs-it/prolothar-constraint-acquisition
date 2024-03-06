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
from prolothar_common import validate

from prolothar_ca.model.ca.dataset import CaDataset
from prolothar_ca.ca.noise_generator.noise_generator import NoiseGenerator
from prolothar_ca.ca.noise_generator.single_example_noise_generator import SingleExampleNoiseGenerator

class NoisyExamplesAdder(NoiseGenerator):
    """
    applies a given noise generator to a given proportion of examples in the dataset
    """

    def __init__(self, noise_proportion: float, noise_generator: SingleExampleNoiseGenerator, random_seed: int|None = None) -> None:
        validate.in_closed_interval(noise_proportion, 0, 1)
        self.__noise_proportion = noise_proportion
        self.__noise_generator = noise_generator
        self.__random = Random(random_seed)
        self.__random_seed = random_seed

    def apply(self, dataset: CaDataset):
        example_list = list(dataset)
        self.__random.shuffle(example_list)
        for example in example_list[:int(self.__noise_proportion * len(dataset))]:
            self.__noise_generator.apply_on_example(example)

    def __repr__(self):
        return f'NoisyExamplesAdder({self.__noise_proportion}, {self.__random_seed}, {self.__noise_generator})'